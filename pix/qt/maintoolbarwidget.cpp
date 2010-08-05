#include "maintoolbarwidget.h"
#include "ui_maintoolbarwidget.h"

MainToolBarWidget::MainToolBarWidget(QWidget *parent) :
    QWidget(parent),
    ui(new Ui::MainToolBarWidget)
{
    ui->setupUi(this);
}

MainToolBarWidget::~MainToolBarWidget()
{
    delete ui;
}

void MainToolBarWidget::changeEvent(QEvent *e)
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
