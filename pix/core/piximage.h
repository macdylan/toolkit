#ifndef PIX_IMAGE_H_
#define PIX_IMAGE_H_

class PixImage {
public:

  enum Type {
    NONE = 0,
    JPG,
    PNG,
    GIF,
    BMP
  };

  PixImage();
  PixImage(int lid, int iid, PixImage::Type type);
  ~PixImage();

private:
  int lid;
  int iid;
  PixImage::Type type;
};

#endif  // PIX_IMAGE_H_

