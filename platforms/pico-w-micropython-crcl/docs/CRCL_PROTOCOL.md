# CRCL v1.1 Managed Application Update Procedure

CRCL is the managed replaceable-application path for this release. v1.1 still targets one application file, `/apps/crcl_app.py`; complete multi-file capability-package transfer is intentionally deferred.

## Wire sequence

```text
CMD 200 CRCL.BEGIN SIZE=2841 CRC32=7A31C492 SHA256=<64 hex digits>
RSP 200 OK
DAT 200 CRCL state=receiving ...
END 200

CMD 201 CRCL.DATA SEQ=0 B64=<base64>
...
CMD 212 CRCL.DATA SEQ=11 B64=<base64>

CMD 213 CRCL.END
RSP 213 OK
DAT 213 CRCL state=verified ...
END 213

CMD 214 CRCL.INSTALL
RSP 214 OK
DAT 214 APP present=True backup=True loaded=True running=True ...
END 214
```

## Transfer invariants

- Incoming bytes are written only to `/staging/crcl_app.py.part`.
- Each DATA chunk must carry exactly the next expected sequence number.
- The target rejects data beyond the declared byte count.
- CRC32 is mandatory.
- SHA-256 is optional on the wire; the supplied host uploader sends it.
- `compile()` must accept the staged source before installation.
- The target never treats a partially written DATA append as committed.

## v1.1 durable DATA recovery

The former single JSON journal is replaced by two alternating journal slots. Each slot contains:

- monotonically increasing journal generation;
- CRC32 over the exact JSON payload bytes;
- declared file metadata;
- committed byte count and next sequence number;
- an optional pending-chunk record.

Before appending a DATA chunk, the target persists:

```text
pending.seq
pending.length
pending.crc32
```

After reboot the runtime reconciles the pending record with the actual staged-file length:

- **no append:** stage size equals committed offset → clear pending and expect the same sequence again;
- **complete append:** stage size equals committed offset + pending length and the tail CRC matches → commit the chunk;
- **partial/garbled append:** restore the staged file to the last committed prefix → expect the same sequence again.

The host still performs explicit `--resume`; the target does not silently repeat uncertain traffic.

## Install transaction

After `CRCL.END` verifies the candidate, `CRCL.INSTALL` uses a second recovery boundary:

1. Compile staged source again.
2. Stop the current app.
3. Persist an install transaction marker.
4. Preserve the previous rollback generation, if any.
5. Move active app to backup.
6. Promote staged candidate to active.
7. Load candidate and run `health(ctx)`.
8. Start the application.
9. Remove the install marker **last** to commit.

If reset/power loss occurs while the marker still exists, the next boot treats the candidate as uncommitted and conservatively restores the pre-install application when available.

## Why no silent retransmission?

An embedded control system should not guess whether a command committed. File DATA chunks are recoverable because the node records exact sequence and byte state. Physical output commands are more consequential: the gateway should not repeat an actuator action merely because its reply was lost.

## Security boundary

CRCL protects update integrity and recovery state; it is not a hostile-code sandbox. A managed application is trusted Python executing in the same interpreter as the resident runtime.
