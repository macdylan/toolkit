#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

namespace Ui {
    class MainWindow;
}

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    MainWindow(QWidget *parent = 0);
    ~MainWindow();

protected:
    void changeEvent(QEvent *e);

private:
    Ui::MainWindow *ui;


private slots:
    void on_actionShow_Sidebar_triggered(bool checked);
    void on_actionFull_Screen_triggered(bool checked);
};

#endif // MAINWINDOW_H
