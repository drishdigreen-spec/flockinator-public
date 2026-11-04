#pragma once
// Portable host implementation only: production Mbed TLS MD/HMAC and SHA-256.
// Deliberately excludes ESP hardware accelerators and platform substitutions.
#define MBEDTLS_MD_C
#define MBEDTLS_SHA256_C
