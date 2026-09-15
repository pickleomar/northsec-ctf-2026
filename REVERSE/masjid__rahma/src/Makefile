cc = gcc

cflags  = -Wall -Wextra -fPIE -O2
ldflags = -pie -Wl,-z,relro,-z,now

all: masjid_rahma

masjid_rahma: masjid_os_hard.c banner.h
	$(cc) $(cflags) $(ldflags) masjid_os_easy.c -o masjid_rahma
	strip masjid_rahma

clean:
	rm -f masjid_rahma

.PHONY: all clean

