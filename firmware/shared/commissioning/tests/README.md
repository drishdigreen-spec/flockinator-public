# Commissioning wire and authentication regression tests

These host tests include the **production `crypto.h`** unchanged and compile the real portable `md.c`, `sha256.c`, and `platform_util.c` sources already installed with ESP-IDF. No replacement hash implementation, networking, device access, package installation, or PlatformIO build is involved. A minimal host-only configuration enables MD/HMAC and SHA-256; ESP hardware acceleration is deliberately excluded.

Validated on 13 October 2026: CMake build succeeded and CTest passed its one executable, containing **174 checks**. The local run log is `$HOME/.cache/flockinator-commissioning-crypto/Testing/Temporary/LastTest.log`.

Run from `/Volumes/devops/flockinator`:

```sh
cmake -S firmware/shared/commissioning/tests -B "$HOME/.cache/flockinator-commissioning-crypto" -DMBEDTLS_SOURCE_DIR="$HOME/.platformio/packages/framework-espidf/components/mbedtls/mbedtls"
cmake --build "$HOME/.cache/flockinator-commissioning-crypto"
ctest --test-dir "$HOME/.cache/flockinator-commissioning-crypto" --output-on-failure
"$HOME/.cache/flockinator-commissioning-crypto/test_crypto"
```

Coverage:

- RFC 4231 HMAC-SHA256 test case 1 against its published expected digest.
- Production frame signing against an independent fixed wire/HMAC vector.
- Successful authentication and exact decoded fields.
- Every single-byte mutation across header, identities, nonce, sequence, payload and tag.
- Wrong key, every truncation, trailing data and null input.
- A new correctly signed challenge and recovery after rejected inputs.

The fixed wire vector uses key bytes `00..1f`, sender `00:11:22:33:44:55`, recipient `00:11:22:33:44:55`, nonce `00..0f`, kind DATA, sequence `0x12345678`, and payload `00000000e90900ff`. The expected tag is `9b0ac06ef8deb89ced67578610bad7aff0476be84e04eec12af4daceb76af13c`, independently calculated with Python's standard-library `hmac` and SHA-256.

These tests establish cryptographic framing and tamper rejection. Replay/session policy, OTA flash operations, concurrency and physical radio delivery require separate state-machine or hardware tests. In particular, a correctly authenticated old frame remains cryptographically authentic; freshness is enforced by its caller.
