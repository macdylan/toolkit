#include "piximage.h"

PixImage::PixImage() : lid(-1), iid(-1), type(PixImage::NONE) {
}

PixImage::PixImage(int library_id, int image_id, PixImage::Type image_type)
  : lid(library_id), iid(image_id), type(image_type) {
}

PixImage::~PixImage() {
}
