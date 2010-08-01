#include "mainwindow.h"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);
}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::changeEvent(QEvent *e)
{
    QMainWindow::changeEvent(e);
    switch (e->type()) {
    case QEvent::LanguageChange:
        ui->retranslateUi(this);
        break;
    default:
        break;
    }
}

void MainWindow::on_actionFull_Screen_triggered(bool checked)
{
    if (checked) {
        this->showFullScreen();
    } else {
        this->showNormal();
    }
}

void MainWindow::on_actionShow_Sidebar_triggered(bool checked)
{
    if (checked) {
        this->ui->mainSidebar->show();
    } else {
        this->ui->mainSidebar->hide();
    }
}
