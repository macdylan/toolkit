#include "mainsidebar.h"
#include "ui_mainsidebar.h"

MainSidebar::MainSidebar(QWidget *parent) :
    QFrame(parent),
    ui(new Ui::MainSidebar)
{
    ui->setupUi(this);
}

MainSidebar::~MainSidebar()
{
    delete ui;
}

void MainSidebar::changeEvent(QEvent *e)
{
    QFrame::changeEvent(e);
    switch (e->type()) {
    case QEvent::LanguageChange:
        ui->retranslateUi(this);
        break;
    default:
        break;
    }
}
