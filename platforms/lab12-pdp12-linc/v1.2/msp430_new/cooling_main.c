/*
 * PDP-12-Inspired Digital Cooling Laboratory / MSP430G2553
 * ---------------------------------------------------------
 * NEW INTEGRATION PROGRAM. Original textbook sources are not modified.
 *
 * Learning objectives:
 * 1. Acquire an actual DS18B20 scratchpad and 64-bit sensor ROM.
 * 2. Report raw evidence as well as decoded temperature.
 * 3. Accept controlled commands from a separate instrument (Pico W).
 * 4. Expose a hardware sampling-complete marker on P2.0.
 *
 * Safety: educational demonstration only. P1.0/P1.6 drive onboard LEDs,
 * NOT actuators or mains-powered loads. Candidate sensor/1-Wire timing must
 * be checked on the bench before measurements are treated as evidence.
 *
 * Connections: DS18B20 DQ=P1.7, 4.7k to 3.3V, VDD=3.3V, GND=GND.
 * P1.2 TX -> Pico GP1 RX; P1.1 RX <- Pico GP0 TX; common GND.
 * P2.0 -> Pico GP2 (optional timing event), common GND.
 * External sensor supply ONLY: parasite power NOT supported.
 * UART: 9600 baud, 8N1, 1 MHz calibrated DCO.
 *
 * Protocol out (legacy-compatible):
 * SEQ_HEX=0001,STATUS=0,STATE=1,X16_HEX=02F0,ROM=...,SCRATCH=...,INJECT=0
 * Extra lines: DEVICE,READY,COOLING_V1 / STATUS,STARTED / ACK,RATE,1500
 * Protocol in, ASCII one command per LF, case-sensitive:
 * START, STOP, PING, RATE=1000..60000, FAULT=0|1|2 (for instruction only).
 *
 * Scheduling: nominal period. A full-resolution DS18B20 conversion can take
 * up to 750 ms. The timing marker is after the scratchpad is read, NOT the
 * exact instant at which the physical temperature was sampled.
 */
#include <msp430.h>
#include <stdint.h>
#include "vendor/05_thermostat_logic.h"
#include "vendor/12_sensor_evidence.h"
#include "vendor/06_ds18b20_decode.h"

#define UART_RX_CAP 32u
#define MIN_PERIOD_MS 1000u
#define MAX_PERIOD_MS 60000u

void ow_init(void);
unsigned int ow_reset(void);
void ow_write_byte(uint8_t value);
uint8_t ow_read_byte(void);

static void wait_conversion(void) { __delay_cycles(750000UL); }
static const sensor_bus_t bus = {
    ow_reset, ow_write_byte, ow_read_byte, wait_conversion
};
static sensor_evidence_t evidence;

/* Shared with the interrupt: volatile prevents compiler caching. */
static volatile char rx_line[UART_RX_CAP];
static volatile uint8_t rx_len=0;
static volatile uint8_t rx_ready=0;
static volatile uint8_t rx_overflow=0;

static uint8_t running=0;
static uint8_t inject_fault=0;
static uint16_t period_ms=1000;
static uint16_t sample_number=0;
static int sample_status=-9;
static control_state_t control_state=CONTROL_FAULT;

static void tx_char(char c) {
    while (!(IFG2 & UCA0TXIFG)) { }
    UCA0TXBUF=(unsigned char)c;
}
static void tx_text(const char *p) { while (*p) tx_char(*p++); }
static void tx_hex8(uint8_t v) {
    static const char x[]="0123456789ABCDEF";
    tx_char(x[v>>4]); tx_char(x[v&0x0F]);
}
static void tx_hex16(uint16_t v) { tx_hex8((uint8_t)(v>>8)); tx_hex8((uint8_t)v); }
static void tx_uint(uint16_t v) {
    char buf[6]; uint8_t i=0;
    do { buf[i++]=(char)('0'+v%10u); v/=10u; } while(v && i<6u);
    while(i) tx_char(buf[--i]);
}
static void tx_signed(int value) {
    if (value<0) { tx_char('-'); tx_uint((uint16_t)(-value)); }
    else tx_uint((uint16_t)value);
}
static void uart_init(void) {
    P1SEL |= BIT1|BIT2; P1SEL2 |= BIT1|BIT2;
    UCA0CTL1=UCSWRST|UCSSEL_2;
    UCA0BR0=104; UCA0BR1=0; UCA0MCTL=UCBRS0;
    UCA0CTL1 &= (uint8_t)~UCSWRST;
    IE2 |= UCA0RXIE;
}
/* Buffered receive: the Pico can send a command during a 750 ms conversion.
 * The ISR must be tiny; all parsing occurs outside the interrupt.
 * A second command received before the first is processed is dropped.
 */
#pragma vector=USCIAB0RX_VECTOR
__interrupt void uart_rx_isr(void) {
    char c=(char)UCA0RXBUF;
    if(rx_ready) return;
    if(c=='\r') return;
    if(c=='\n') {
        if(!rx_overflow) { rx_line[rx_len]='\0'; rx_ready=1; }
        else { rx_overflow=0; rx_len=0; }
        return;
    }
    if(rx_len < UART_RX_CAP-1u) rx_line[rx_len++]=c;
    else rx_overflow=1;
}
static uint8_t equal(const char *a,const char *b) {
    while(*a && *b) if(*a++!=*b++) return 0;
    return (uint8_t)(*a==*b);
}
static uint8_t starts(const char *a, const char *prefix) {
    while(*prefix) if(*a++!=*prefix++) return 0;
    return 1;
}
static uint8_t parse_rate(const char *p, uint16_t *out) {
    uint32_t v=0; uint8_t digits=0;
    while(*p) {
        if(*p<'0' || *p>'9') return 0;
        v=v*10u+(uint32_t)(*p++-'0'); ++digits;
        if(v>MAX_PERIOD_MS) return 0;
    }
    if(!digits || v<MIN_PERIOD_MS) return 0;
    *out=(uint16_t)v;
    return 1;
}
static void process_command(void) {
    char cmd[UART_RX_CAP]; uint8_t i; uint16_t requested=0;
    if(!rx_ready) return;
    /* Copy and clear under a brief critical section. */
    __disable_interrupt();
    for(i=0; i<=rx_len && i<UART_RX_CAP; ++i) cmd[i]=rx_line[i];
    rx_len=0; rx_ready=0;
    __enable_interrupt();
    if(equal(cmd,"START")) { running=1; tx_text("ACK,START\r\n"); }
    else if(equal(cmd,"STOP")) { running=0; tx_text("ACK,STOP\r\n"); }
    else if(equal(cmd,"PING")) { tx_text("ACK,PONG\r\n"); }
    else if(starts(cmd,"RATE=") && parse_rate(cmd+5,&requested)) {
        period_ms=requested;
        tx_text("ACK,RATE,"); tx_uint(period_ms); tx_text("\r\n");
    }
    else if(equal(cmd,"FAULT=0") || equal(cmd,"FAULT=1") || equal(cmd,"FAULT=2")) {
        inject_fault=(uint8_t)(cmd[6]-'0');
        tx_text("ACK,FAULT,"); tx_uint(inject_fault); tx_text("\r\n");
    } else tx_text("ERROR,BAD_COMMAND\r\n");
}
static void outputs(control_state_t s) {
    if(s==CONTROL_ON) P1OUT |= BIT0; else P1OUT &= (uint8_t)~BIT0;
    if(s==CONTROL_FAULT) P1OUT |= BIT6; else P1OUT &= (uint8_t)~BIT6;
}
static void report(void) {
    uint8_t i;
    tx_text("SEQ_HEX="); tx_hex16(sample_number);
    tx_text(",STATUS="); tx_signed(sample_status);
    tx_text(",STATE="); tx_uint((uint16_t)control_state);
    tx_text(",X16_HEX="); tx_hex16((uint16_t)evidence.temperature_x16);
    tx_text(",ROM=");
    if(evidence.rom_captured) for(i=0;i<8u;++i) tx_hex8(evidence.rom[i]);
    else tx_text("NA");
    tx_text(",SCRATCH=");
    if(evidence.scratch_captured) for(i=0;i<9u;++i) tx_hex8(evidence.scratchpad[i]);
    else tx_text("NA");
    tx_text(",INJECT="); tx_uint(inject_fault); tx_text("\r\n");
}
/* Nominal millisecond wait: duration is an approximate DCO time, not a
 * calibrated high-resolution clock. Running RX interrupts remain enabled.
 */
static void wait_ms(uint16_t ms) {
    while(ms--) {
        __delay_cycles(1000UL);
        process_command();
        if(!running) return;
    }
}
static void capture_once(void) {
    int16_t discarded=0;
    ++sample_number;
    if(inject_fault==2u) {
        evidence.rom_captured=0; evidence.scratch_captured=0;
        evidence.temperature_x16=0;
        sample_status=-6; /* fake stale reading, clearly flagged */
    } else {
        sample_status=sensor_capture(&bus,&evidence);
        if(inject_fault==1u && evidence.scratch_captured) {
            evidence.scratchpad[8]^=1u;
            sample_status=ds18b20_decode_x16(evidence.scratchpad,&discarded);
        }
    }
    control_state=control_step(control_state,evidence.temperature_x16,(uint8_t)(sample_status==0));
    outputs(control_state);
    /* A 1 ms observable marker. The Pico timestamps the rising edge. */
    P2OUT |= BIT0;
    __delay_cycles(1000UL);
    P2OUT &= (uint8_t)~BIT0;
    report();
}
int main(void) {
    uint16_t rest;
    WDTCTL=WDTPW|WDTHOLD;
    if(CALBC1_1MHZ==0xff || CALDCO_1MHZ==0xff) for(;;) { }
    DCOCTL=0; BCSCTL1=CALBC1_1MHZ; DCOCTL=CALDCO_1MHZ;
    BCSCTL2 &= (uint8_t)~(SELS|DIVS_3);
    P1SEL &= (uint8_t)~(BIT0|BIT6);
    P1SEL2 &= (uint8_t)~(BIT0|BIT6);
    P1OUT &= (uint8_t)~(BIT0|BIT6); P1DIR|=BIT0|BIT6;
    P2SEL &= (uint8_t)~BIT0; P2SEL2 &= (uint8_t)~BIT0;
    P2OUT &= (uint8_t)~BIT0; P2DIR|=BIT0;
    outputs(CONTROL_FAULT);
    uart_init(); ow_init();
    __enable_interrupt();
    tx_text("DEVICE,READY,COOLING_V1\r\n");
    for(;;) {
        process_command();
        if(!running) { __delay_cycles(10000UL); continue; }
        capture_once();
        /* 750 ms conversion + small transport overhead; nominal target. */
        rest=(period_ms>750u)? (uint16_t)(period_ms-750u):0u;
        wait_ms(rest);
    }
}
