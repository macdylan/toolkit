#include "mainsidebar.h"
#include "ui_mainsidebar.h"

#include "sidebarmodel.h"
#include "sidebardelegate.h"

MainSidebar::MainSidebar(QWidget *parent) :
    QFrame(parent),
    ui(new Ui::MainSidebar)
{
    ui->setupUi(this);
    ui->treeView->setModel(new SidebarModel());
    ui->treeView->setItemDelegate(new SidebarDelegate());
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
