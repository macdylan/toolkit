#ifndef SLIDESHOW_H
#define SLIDESHOW_H

#include <QWidget>

namespace Ui {
    class SlideShow;
}

class SlideShow : public QWidget {
    Q_OBJECT
public:
    SlideShow(QWidget *parent = 0);
    ~SlideShow();

protected:
    void changeEvent(QEvent *e);

private:
    Ui::SlideShow *ui;
};

#endif // SLIDESHOW_H
