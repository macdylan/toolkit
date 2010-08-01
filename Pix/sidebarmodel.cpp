#include "sidebarmodel.h"

SidebarModel::SidebarModel()
{
    
}

QVariant SidebarModel::data(const QModelIndex& index, int role) const {
    if (index.isValid() == false) {
        return QVariant();
    }

    if (role == Qt::DisplayRole) {
        return tr("TODO");
    } else if (role == Qt::ToolTipRole) {
        return tr("TODO");
    } else if (role == Qt::DecorationRole) {
        return tr("TODO");
    }

    return QVariant();
}

QModelIndex SidebarModel::index(int row, int column, const QModelIndex& parent) const {
    return createIndex(row, column, parent.isValid() ? parent.row() : 0);
}

QModelIndex SidebarModel::parent(const QModelIndex& idx) const {
    if (idx.internalId() == 0) {
        return QModelIndex();
    } else {
        return index(idx.internalId(), 0);
    }
}

int SidebarModel::rowCount(const QModelIndex &parent) const {
    return 10;
}

