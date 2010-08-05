#include "slideshow.h"
#include "ui_slideshow.h"

SlideShow::SlideShow(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::SlideShow)
{
    ui->setupUi(this);
}

SlideShow::~SlideShow()
{
    delete ui;
}

void SlideShow::changeEvent(QEvent *e)
{
    QWidget::changeEvent(e);
    switch (e->type()) {
    case QEvent::LanguageChange:
        ui->retranslateUi(this);
        break;
    default:
        break;
    }
}
