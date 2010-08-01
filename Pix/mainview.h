#ifndef MAINVIEW_H
#define MAINVIEW_H

#include <QFrame>

namespace Ui {
    class MainView;
}

class MainView : public QFrame {
    Q_OBJECT
public:
    MainView(QWidget *parent = 0);
    ~MainView();

protected:
    void changeEvent(QEvent *e);

private:
    Ui::MainView *ui;
};

#endif // MAINVIEW_H
