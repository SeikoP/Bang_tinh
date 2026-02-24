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
        anchors.margins: 16
        spacing: 12

        // Header
        RowLayout {
            Layout.fillWidth: true
            spacing: 12

            Label {
                text: "📊 Kho hàng"
                font.pixelSize: 18
                font.weight: Font.Medium
                color: "#1F2937"
            }

            Item { Layout.fillWidth: true }

            SearchField {
                id: stockSearch
                Layout.preferredWidth: 250
                placeholderText: "Tìm sản phẩm..."
            }
        }

        // ── Two-panel layout: Stock list (left) + Change log (right) ──
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            // Stock list
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 2  // 2:1 ratio
                radius: 12
                border.width: 1
                border.color: "#E5E7EB"
                clip: true

                ListView {
                    id: stockListView
                    anchors.fill: parent
                    anchors.margins: 8
                    clip: true
                    model: stockVM.stockItems
                    spacing: 4

                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: Rectangle {
                        width: stockListView.width
                        height: 60
                        radius: 10
                        color: stockItemMouse.containsMouse ? "#F3F4F6" : "white"

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 16
                            anchors.rightMargin: 16
                            spacing: 12

                            // Product info
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2

                                Label {
                                    text: model.name || ""
                                    font.pixelSize: 14
                                    font.weight: Font.Medium
                                    color: "#1F2937"
                                }

                                Label {
                                    text: (model.largeUnit || "") + " × " + (model.conversion || 1)
                                    font.pixelSize: 11
                                    color: "#6B7280"
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
                                    Material.background: "#fee2e2"
                                    Material.foreground: "#DC2626"
                                    onClicked: stockVM.adjustQuantity(index, -1)
                                }

                                // Quantity display
                                Rectangle {
                                    width: 56; height: 36
                                    color: "#F3F4F6"
                                    radius: 4

                                    Label {
                                        anchors.centerIn: parent
                                        text: model.quantity !== undefined ? model.quantity.toString() : "0"
                                        font.pixelSize: 16
                                        font.weight: Font.Bold
                                        color: "#1F2937"
                                    }
                                }

                                // Increase
                                RoundButton {
                                    text: "+"
                                    font.pixelSize: 18
                                    width: 36; height: 36
                                    Material.background: "#d1fae5"
                                    Material.foreground: "#047857"
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
                Layout.preferredWidth: 1  // 2:1 ratio
                radius: 12
                border.width: 1
                border.color: "#E5E7EB"
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8

                    Label {
                        text: "📋 Lịch sử thay đổi"
                        font.pixelSize: 14
                        font.weight: Font.Medium
                        color: "#1F2937"
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#E5E7EB"
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
                            radius: 6
                            color: index % 2 === 0 ? "white" : "#F9FAFB"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 8
                                anchors.rightMargin: 8
                                spacing: 6

                                Label {
                                    text: model.changeType === "increase" ? "📈" : "📉"
                                    font.pixelSize: 14
                                }

                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 0

                                    Label {
                                        text: model.productName || ""
                                        font.pixelSize: 12
                                        font.weight: Font.Medium
                                        color: "#1F2937"
                                        elide: Text.ElideRight
                                    }

                                    Label {
                                        text: (model.oldQty || 0) + " → " + (model.newQty || 0)
                                        font.pixelSize: 10
                                        color: "#6B7280"
                                    }
                                }

                                Label {
                                    text: model.changedAt || ""
                                    font.pixelSize: 9
                                    color: "#9CA3AF"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
