import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"
import "../dialogs"

/**
 * StockView — Inventory management with stepper controls.
 */
Item {
    id: stockViewRoot

    Component.onCompleted: stockVM.refreshData()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingMd
        spacing: Theme.spacingSm

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.spacingSm

            Label {
                text: "Kho hàng"
                font: Theme.typography.titleMedium
                color: Theme.backgroundText
            }

            Item { Layout.fillWidth: true }

            SearchField {
                id: stockSearch
                Layout.preferredWidth: 250
                placeholderText: "Tìm sản phẩm..."
                onTextChanged: stockVM.filterProducts(text)
            }
        }

        // Two-panel layout: Stock list (left) + Change log (right)
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: Theme.spacingMd

            // Stock list
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 2
                radius: Theme.radiusLg
                border.width: 1
                border.color: Theme.outline
                clip: true

                ListView {
                    id: stockListView
                    anchors.fill: parent
                    anchors.margins: Theme.spacingSm
                    clip: true
                    model: stockVM.stockItems
                    spacing: Theme.spacingXs

                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: Rectangle {
                        width: stockListView.width
                        height: 60
                        radius: Theme.radiusMd
                        color: stockItemMouse.containsMouse ? Theme.surfaceVariant : Theme.surface

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: Theme.spacingMd
                            anchors.rightMargin: Theme.spacingMd
                            spacing: Theme.spacingSm

                            // Product info
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Label {
                                    text: model.name || ""
                                    font: Theme.typography.labelLarge
                                    color: Theme.backgroundText
                                }

                                Label {
                                    text: (model.largeUnit || "") + " × " + (model.conversion || 1)
                                    font: Theme.typography.labelSmall
                                    color: Theme.surfaceVariantText
                                }
                            }

                            // Stepper control
                            RowLayout {
                                spacing: 0

                                // Decrease
                                RoundButton {
                                    text: "−"
                                    font.pixelSize: 18
                                    width: 36; height: 36
                                    Material.background: Theme.errorContainer
                                    Material.foreground: Theme.error
                                    onClicked: stockVM.adjustQuantity(index, -1)
                                }

                                // Quantity display
                                Rectangle {
                                    width: 56; height: 36
                                    color: Theme.surfaceVariant
                                    radius: Theme.radiusSm

                                    Label {
                                        anchors.centerIn: parent
                                        text: model.quantity !== undefined ? model.quantity.toString() : "0"
                                        font: Theme.typography.titleSmall
                                        color: Theme.backgroundText
                                    }
                                }

                                // Increase
                                RoundButton {
                                    text: "+"
                                    font.pixelSize: 18
                                    width: 36; height: 36
                                    Material.background: Theme.successContainer
                                    Material.foreground: Theme.primaryDark
                                    onClicked: stockVM.adjustQuantity(index, 1)
                                }
                            }
                        }

                        MouseArea {
                            id: stockItemMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            propagateComposedEvents: true
                            onPressed: function(mouse) { mouse.accepted = false }
                        }
                    }
                }
            }

            // Change log panel
            Rectangle {
                Layout.fillHeight: true
                Layout.preferredWidth: 1
                radius: Theme.radiusLg
                border.width: 1
                border.color: Theme.outline
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: Theme.spacingSm

                    RowLayout {
                        Layout.fillWidth: true

                        Label {
                            text: "Lịch sử thay đổi"
                            font: Theme.typography.titleSmall
                            color: Theme.backgroundText
                            Layout.fillWidth: true
                        }

                        Button {
                            text: "Xóa"
                            flat: true
                            font: Theme.typography.labelSmall
                            Material.foreground: Theme.error
                            onClicked: stockVM.clearChangeLog()
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: Theme.outline
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: stockVM.changeLog
                        spacing: 2

                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                        delegate: Rectangle {
                            width: parent ? parent.width : 0
                            height: 40
                            radius: Theme.radiusSm
                            color: index % 2 === 0 ? Theme.surface : Theme.backgroundSecondary

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: Theme.spacingSm
                                anchors.rightMargin: Theme.spacingSm
                                spacing: 6

                                Rectangle {
                                    width: 6; height: 6; radius: 3
                                    color: model.changeType === "increase" ? Theme.success : Theme.error
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 0

                                    Label {
                                        text: model.productName || ""
                                        font: Theme.typography.labelMedium
                                        color: Theme.backgroundText
                                        elide: Text.ElideRight
                                    }

                                    Label {
                                        text: (model.oldQty || 0) + " → " + (model.newQty || 0)
                                        font: Theme.typography.labelSmall
                                        color: Theme.surfaceVariantText
                                    }
                                }

                                Label {
                                    text: model.changedAt || ""
                                    font: Theme.typography.labelSmall
                                    color: Theme.textDisabled
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
