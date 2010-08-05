#ifndef MAINSIDEBAR_H
#define MAINSIDEBAR_H

#include <QFrame>

namespace Ui {
    class MainSidebar;
}

class MainSidebar : public QFrame {
    Q_OBJECT
public:
    MainSidebar(QWidget *parent = 0);
    ~MainSidebar();

protected:
    void changeEvent(QEvent *e);

private:
    Ui::MainSidebar *ui;
};

#endif // MAINSIDEBAR_H
