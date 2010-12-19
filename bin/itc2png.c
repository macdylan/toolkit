// Extract images from iTunes albums art file (with extension .itc2)
// Currently only support .png files, but with minor modification, could support .jpg files, too.
// Author: Santa Zhang (santa1987@gmail.com)

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifndef __APPLE__
#include <malloc.h>
#endif  // __APPLE__

void extract_image(char* itc2_fn) {
  int png_head[] = {0x89, 0x50, 0x4e, 0x47};
  int png_tail[] = {0xae, 0x42, 0x60, 0x82};
  unsigned char buf[4];
  unsigned char ch;
  int i;
  char* extract_fn = (char *) malloc(strlen(itc2_fn) + 20);
  FILE* fin = fopen(itc2_fn, "rb");
  FILE* fout = NULL;
  for (i = 0; i < 4; i++) {
    buf[i] = 0;
  }
  while (!feof(fin)) {
    int png_head_match = 1;
    int png_tail_match = 1;
    ch = fgetc(fin);
    // shift bytes
    for (i = 0; i < 3; i++) {
      buf[i] = buf[i + 1];
    }
    buf[3] = ch;
    for (i = 0; i < 4; i++) {
      if (buf[i] != png_head[i]) {
        png_head_match = 0;
        break;
      }
    }
    for (i = 0; i < 4; i++) {
      if (buf[i] != png_tail[i]) {
        png_tail_match = 0;
        break;
      }
    }
    if (png_head_match == 1) {
      // find a proper file name
      i = 0;
      for (;;) {
        if (i == 0) {
          sprintf(extract_fn, "%s.png", itc2_fn);
        } else {
          sprintf(extract_fn, "%s.%d.png", itc2_fn, i);
        }
        fout = fopen(extract_fn, "rb");
        if (fout != NULL) {
          fclose(fout);
        } else {
          fout = fopen(extract_fn, "wb");
          break;
        }
        i++;
      }
      for (i = 0; i < 4; i++) {
        fputc(buf[i], fout);
      }
    } else if (png_tail_match == 1) {
      fputc(ch, fout);
      fclose(fout);
      fout = NULL;
    } else if (fout != NULL) {
      fputc(ch, fout);
    }
  }
  fclose(fin);
  free(extract_fn);
}

int main(int argc, char* argv[]) {
  if (argc == 1) {
    printf("Usage: itc2png <itc2_file>");
    exit(0);
  }
  extract_image(argv[1]);
  return 0;
}
