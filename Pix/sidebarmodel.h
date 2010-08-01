#ifndef SIDEBARMODEL_H
#define SIDEBARMODEL_H

#include <QAbstractItemModel>

enum SidebarType {
    LibraryLabel = 0,
    LibraryItem,
    OnlineLabel,
    OnlineItem,
    AlbumLabel,
    AlbumFolderItem,
    AlbumItem,
    SmartAlbumItem
};


class SidebarModel : public QAbstractItemModel
{
    Q_OBJECT

public:

    SidebarModel();

    QVariant data(const QModelIndex& index, int role) const;

    QModelIndex index(int row, int column, const QModelIndex& parent = QModelIndex()) const;

    QModelIndex parent(const QModelIndex& index) const;

    int rowCount(const QModelIndex& parent = QModelIndex()) const;

    /** no header, one column always */
    QVariant headerData(int, Qt::Orientation, int) const {
        return QVariant();
    }

    /** no header, one column always */
    int columnCount(const QModelIndex&) const {
        return 1;
    }
};

class SidebarItem {

    SidebarType myType;
    QModelIndex myIndex;

public:

    SidebarItem(const QModelIndex&);

    SidebarType type() const {
        return myType;
    }

};


#endif // SIDEBARMODEL_H
