#include "mainwindow.h"
#include "ui_mainwindow.h"

#include "aboutdialog.h"
#include "preferencesdialog.h"
#include "getinfodialog.h"
#include "maintoolbarwidget.h"

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    this->aboutDialog = new AboutDialog(this);
    this->preferencesDialog = new PreferencesDialog(this);
    this->getInfoDialog = new GetInfoDialog(this);
    this->mainToolBarWidget = new MainToolBarWidget(this);

    this->ui->mainToolBar->addSeparator();
    this->ui->mainToolBar->addWidget(this->mainToolBarWidget);

}

MainWindow::~MainWindow()
{
    delete ui;
    delete aboutDialog;
    delete preferencesDialog;
    delete getInfoDialog;
    delete mainToolBarWidget;
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

void MainWindow::on_actionAbout_triggered()
{
    this->aboutDialog->show();
}

void MainWindow::on_actionPreferences_triggered()
{
    this->preferencesDialog->show();
}

void MainWindow::on_actionGet_Info_triggered()
{
    bool couldGetInfo = true;   // whether there's something selected, so we could display info for it
    if (couldGetInfo) {
        this->getInfoDialog->show();
    }
}

void MainWindow::on_actionShow_Toolbar_triggered(bool checked)
{
    if (checked) {
        this->ui->mainToolBar->show();
    } else {
        this->ui->mainToolBar->hide();
    }
}

void MainWindow::on_actionShow_Status_Bar_triggered(bool checked)
{
    if (checked) {
        this->ui->statusBar->show();
    } else {
        this->ui->statusBar->hide();
    }
}
