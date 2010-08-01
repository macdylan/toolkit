#ifndef GETINFODIALOG_H
#define GETINFODIALOG_H

#include <QDialog>

namespace Ui {
    class GetInfoDialog;
}

class GetInfoDialog : public QDialog {
    Q_OBJECT
public:
    GetInfoDialog(QWidget *parent = 0);
    ~GetInfoDialog();

protected:
    void changeEvent(QEvent *e);

private:
    Ui::GetInfoDialog *ui;
};

#endif // GETINFODIALOG_H
