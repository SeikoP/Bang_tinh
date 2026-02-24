import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"
import "../dialogs"

/**
 * ProductView — Product CRUD + Quick Price management.
 */
Item {
    id: productViewRoot

    Component.onCompleted: productVM.refreshData()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingMd
        spacing: Theme.spacingMd

        // Header
        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "Quản lý Sản phẩm"
                font: Theme.typography.titleMedium
                color: Theme.backgroundText
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "+ Thêm sản phẩm"
                Material.background: Theme.primary
                Material.foreground: Theme.primaryText
                onClicked: productDialog.openForNew()
            }
        }

        // Product cards list
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: productVM.products
            spacing: Theme.spacingSm

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                width: parent ? parent.width : 0
                height: 72
                radius: Theme.radiusLg
                color: prodCardMouse.containsMouse ? Theme.surfaceVariant : Theme.surface
                border.width: 1
                border.color: Theme.divider

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Theme.spacingMd
                    anchors.rightMargin: Theme.spacingMd
                    spacing: Theme.spacingSm

                    // Favorite
                    Rectangle {
                        width: 32; height: 32; radius: 16
                        color: model.isFavorite ? Theme.withAlpha(Theme.warningColor, 0.15) : Theme.surfaceVariant

                        Label {
                            anchors.centerIn: parent
                            text: model.isFavorite ? "★" : "☆"
                            font.pixelSize: 16
                            color: model.isFavorite ? Theme.warningColor : Theme.textDisabled
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: productVM.toggleFavorite(model.productId)
                        }
                    }

                    // Product info
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: model.name || ""
                            font: Theme.typography.labelLarge
                            color: Theme.backgroundText
                        }

                        RowLayout {
                            spacing: Theme.spacingSm
                            Label {
                                text: "ĐV: " + (model.largeUnit || "")
                                font: Theme.typography.bodySmall; color: Theme.surfaceVariantText
                            }
                            Label {
                                text: "Quy đổi: " + (model.conversion || 1)
                                font: Theme.typography.bodySmall; color: Theme.surfaceVariantText
                            }
                        }
                    }

                    // Price
                    Label {
                        text: model.unitPrice ? Number(model.unitPrice).toLocaleString('vi-VN') + " đ" : ""
                        font: Theme.typography.titleSmall
                        color: Theme.primary
                    }

                    // Active badge
                    Rectangle {
                        width: badgeLabel.implicitWidth + 16
                        height: 24
                        radius: 12
                        color: model.isActive ? Theme.successContainer : Theme.errorContainer

                        Label {
                            id: badgeLabel
                            anchors.centerIn: parent
                            text: model.isActive ? "Active" : "Inactive"
                            font: Theme.typography.labelSmall
                            color: model.isActive ? Theme.primaryDark : Theme.error
                        }
                    }

                    // Edit button
                    RoundButton {
                        text: "Sửa"
                        width: 48; height: 36
                        flat: true
                        font: Theme.typography.labelSmall
                        onClicked: {
                            productDialog.openForEdit(model.productId, model.name, model.largeUnit, model.conversion, model.unitPrice)
                        }
                    }

                    // Delete button
                    RoundButton {
                        text: "Xóa"
                        width: 48; height: 36
                        flat: true
                        font: Theme.typography.labelSmall
                        Material.foreground: Theme.error
                        onClicked: {
                            deleteConfirm.show("Xóa sản phẩm?", "Sản phẩm '" + model.name + "' sẽ bị vô hiệu hóa.", function() {
                                productVM.deleteProduct(model.productId)
                            })
                        }
                    }
                }

                MouseArea {
                    id: prodCardMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    propagateComposedEvents: true
                    onPressed: function(mouse) { mouse.accepted = false }
                }
            }
        }

        // Quick Price section
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 140
            radius: Theme.radiusLg
            border.width: 1
            border.color: Theme.outline

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: Theme.spacingSm

                RowLayout {
                    Label {
                        text: "Giá nhanh"
                        font: Theme.typography.titleSmall
                        color: Theme.backgroundText
                    }
                    Item { Layout.fillWidth: true }
                    Button {
                        text: "+ Thêm"
                        flat: true
                        font: Theme.typography.labelSmall
                        Material.foreground: Theme.primary
                        onClicked: {
                            // TODO: open quick price add dialog
                        }
                    }
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: Theme.spacingSm

                    Repeater {
                        model: productVM.quickPrices

                        delegate: Rectangle {
                            width: qpLabel.implicitWidth + 24
                            height: 32
                            radius: Theme.radiusMd
                            color: qpMouse.containsMouse ? Theme.primaryContainer : Theme.surfaceVariant

                            Label {
                                id: qpLabel
                                anchors.centerIn: parent
                                text: (model.name || "") + ": " + (model.price ? Number(model.price).toLocaleString('vi-VN') : "0") + "đ"
                                font: Theme.typography.labelMedium
                                color: Theme.primaryDark
                            }

                            MouseArea {
                                id: qpMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                            }
                        }
                    }
                }
            }
        }
    }

    ProductDialog { id: productDialog }
    ConfirmDialog { id: deleteConfirm }

    Connections {
        target: productVM
        function onProductAdded() { globalToast.show("Đã thêm sản phẩm!", "success") }
        function onProductDeleted() { globalToast.show("Đã xóa sản phẩm", "info") }
    }
}
