#ifndef MAINTOOLBARWIDGET_H
#define MAINTOOLBARWIDGET_H

#include <QWidget>

namespace Ui {
    class MainToolBarWidget;
}

class MainToolBarWidget : public QWidget {
    Q_OBJECT
public:
    MainToolBarWidget(QWidget *parent = 0);
    ~MainToolBarWidget();

protected:
    void changeEvent(QEvent *e);

private:
    Ui::MainToolBarWidget *ui;
};

#endif // MAINTOOLBARWIDGET_H
