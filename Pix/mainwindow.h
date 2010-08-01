#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

class AboutDialog;
class PreferencesDialog;
class GetInfoDialog;

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

    AboutDialog *aboutDialog;
    PreferencesDialog *preferencesDialog;
    GetInfoDialog *getInfoDialog;

private slots:
    void on_actionShow_Status_Bar_triggered(bool checked);
    void on_actionShow_Toolbar_triggered(bool checked);
    void on_actionGet_Info_triggered();
    void on_actionPreferences_triggered();
    void on_actionAbout_triggered();
    void on_actionShow_Sidebar_triggered(bool checked);
    void on_actionFull_Screen_triggered(bool checked);
};

#endif // MAINWINDOW_H
