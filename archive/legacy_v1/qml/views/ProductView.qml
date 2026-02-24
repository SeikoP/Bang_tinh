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
        anchors.margins: 16
        spacing: 16

        // Header
        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "📦 Quản lý Sản phẩm"
                font.pixelSize: 18
                font.weight: Font.Medium
                color: "#1F2937"
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "+ Thêm sản phẩm"
                Material.background: "#10b981"
                Material.foreground: "white"
                onClicked: {
                    productDialog.editMode = false
                    productDialog.clear()
                    productDialog.open()
                }
            }
        }

        // Product cards list
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: productVM.products
            spacing: 8

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                width: parent ? parent.width : 0
                height: 72
                radius: 12
                color: prodCardMouse.containsMouse ? "#F3F4F6" : "white"
                border.width: 1
                border.color: "#F3F4F6"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 16
                    anchors.rightMargin: 16
                    spacing: 12

                    // Favorite
                    Label {
                        text: model.isFavorite ? "⭐" : "☆"
                        font.pixelSize: 20
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
                            font.pixelSize: 15
                            font.weight: Font.Medium
                            color: "#1F2937"
                        }

                        RowLayout {
                            spacing: 12
                            Label {
                                text: "ĐV: " + (model.largeUnit || "")
                                font.pixelSize: 12; color: "#6B7280"
                            }
                            Label {
                                text: "Quy đổi: " + (model.conversion || 1)
                                font.pixelSize: 12; color: "#6B7280"
                            }
                        }
                    }

                    // Price
                    Label {
                        text: model.unitPrice ? Number(model.unitPrice).toLocaleString('vi-VN') + " đ" : ""
                        font.pixelSize: 16
                        font.weight: Font.Bold
                        color: "#10B981"
                    }

                    // Active badge
                    Rectangle {
                        width: badgeLabel.implicitWidth + 16
                        height: 24
                        radius: 12
                        color: model.isActive ? "#d1fae5" : "#fee2e2"

                        Label {
                            id: badgeLabel
                            anchors.centerIn: parent
                            text: model.isActive ? "Active" : "Inactive"
                            font.pixelSize: 11
                            font.weight: Font.Medium
                            color: model.isActive ? "#047857" : "#DC2626"
                        }
                    }

                    // Edit button
                    RoundButton {
                        text: "✏️"
                        width: 36; height: 36
                        flat: true
                        onClicked: {
                            productDialog.editMode = true
                            productDialog.loadProduct(model.productId, model.name, model.largeUnit, model.conversion, model.unitPrice)
                            productDialog.open()
                        }
                    }

                    // Delete button
                    RoundButton {
                        text: "🗑️"
                        width: 36; height: 36
                        flat: true
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

        // ── Quick Price section ──
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 140
            radius: 12
            border.width: 1
            border.color: "#E5E7EB"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                RowLayout {
                    Label {
                        text: "💰 Giá nhanh"
                        font.pixelSize: 14
                        font.weight: Font.Medium
                        color: "#1F2937"
                    }
                    Item { Layout.fillWidth: true }
                }

                Flow {
                    Layout.fillWidth: true
                    spacing: 8

                    Repeater {
                        model: productVM.quickPrices

                        delegate: Rectangle {
                            width: qpLabel.implicitWidth + 24
                            height: 32
                            radius: 8
                            color: qpMouse.containsMouse ? "#d1fae5" : "#F3F4F6"

                            Label {
                                id: qpLabel
                                anchors.centerIn: parent
                                text: (model.name || "") + ": " + (model.price ? Number(model.price).toLocaleString('vi-VN') : "0") + "đ"
                                font.pixelSize: 12
                                font.weight: Font.Medium
                                color: "#047857"
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
        function onProductAdded() { globalToast.show("✅ Đã thêm sản phẩm!", "success") }
        function onProductDeleted() { globalToast.show("🗑️ Đã xóa sản phẩm", "info") }
    }
}
