#include "getinfodialog.h"
#include "ui_getinfodialog.h"

GetInfoDialog::GetInfoDialog(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::GetInfoDialog)
{
    this->setWindowFlags(Qt::Dialog | Qt::CustomizeWindowHint | Qt::WindowTitleHint | Qt::WindowCloseButtonHint);
    ui->setupUi(this);  // set up the UI after setWindowFlags, so that the WindowTitle will be correctly displayed
    this->setFixedSize(this->size());   // make the dialog unsizable, this should be after setupUi(), which loads designed window size
}

GetInfoDialog::~GetInfoDialog()
{
    delete ui;
}

void GetInfoDialog::changeEvent(QEvent *e)
{
    QDialog::changeEvent(e);
    switch (e->type()) {
    case QEvent::LanguageChange:
        ui->retranslateUi(this);
        break;
    default:
        break;
    }
}
