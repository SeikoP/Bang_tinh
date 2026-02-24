import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"
import "../dialogs"

/**
 * CalculationView — Main shift management view.
 * Two tabs: "Tính tiền" (calculation table) + "Danh sách SP" (product list)
 */
Item {
    id: calcViewRoot

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── Tab Bar ──
        TabBar {
            id: calcTabBar
            Layout.fillWidth: true
            Material.accent: "#10b981"

            TabButton {
                text: "🧮 Tính tiền"
                font.pixelSize: 14
                width: implicitWidth
            }

            TabButton {
                text: "📦 Danh sách Sản phẩm"
                font.pixelSize: 14
                width: implicitWidth
            }
        }

        // ── Tab Content ──
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: calcTabBar.currentIndex

            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // TAB 0: Calculation Table
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    // Header row with total
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 16

                        Label {
                            text: "📊 Bảng tính ca"
                            font.pixelSize: 18
                            font.weight: Font.Medium
                            color: "#1F2937"
                        }

                        Item { Layout.fillWidth: true }

                        // Total amount card
                        Rectangle {
                            Layout.preferredWidth: totalLabel.implicitWidth + 40
                            Layout.preferredHeight: 44
                            radius: 12
                            color: Qt.rgba(0.063, 0.725, 0.506, 0.1)
                            border.width: 1
                            border.color: Qt.rgba(0.063, 0.725, 0.506, 0.3)

                            RowLayout {
                                anchors.centerIn: parent
                                spacing: 8

                                Label {
                                    text: "Tổng:"
                                    font.pixelSize: 14
                                    color: "#047857"
                                }

                                Label {
                                    id: totalLabel
                                    text: calculationVM.formatTotal() + " đ"
                                    font.pixelSize: 18
                                    font.weight: Font.Bold
                                    color: "#047857"
                                }
                            }
                        }

                        // Action buttons
                        Button {
                            text: "💾 Lưu ca"
                            Material.background: "#10b981"
                            Material.foreground: "white"
                            font.pixelSize: 13
                            onClicked: saveSessionDialog.open()
                        }

                        Button {
                            text: "🔄 Reset"
                            Material.background: "#F3F4F6"
                            Material.foreground: "#374151"
                            font.pixelSize: 13
                            onClicked: resetConfirm.show(
                                "Reset ca?",
                                "Đặt lại tất cả số lượng về 0. Thao tác này không thể hoàn tác.",
                                function() { calculationVM.resetSession() }
                            )
                        }
                    }

                    // ── Session Table ──
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: 12
                        border.width: 1
                        border.color: "#E5E7EB"
                        clip: true

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0

                            // Table Header
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 44
                                color: "#F9FAFB"

                                Rectangle {
                                    anchors.bottom: parent.bottom
                                    width: parent.width; height: 1; color: "#E5E7EB"
                                }

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12
                                    spacing: 0

                                    Label { Layout.preferredWidth: 36; text: "#"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.fillWidth: true; Layout.minimumWidth: 160; text: "Sản phẩm"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280" }
                                    Label { Layout.preferredWidth: 60; text: "ĐV lớn"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 50; text: "Quy đổi"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 80; text: "Đơn giá"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; horizontalAlignment: Text.AlignRight }
                                    Label { Layout.preferredWidth: 100; text: "SL Giao"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 100; text: "SL Đóng"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 60; text: "Đã dùng"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 100; text: "Thành tiền"; font.pixelSize: 12; font.weight: Font.Medium; color: "#6B7280"; horizontalAlignment: Text.AlignRight }
                                }
                            }

                            // Table Body
                            ListView {
                                id: sessionListView
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                clip: true
                                model: calculationVM.sessionItems
                                boundsBehavior: Flickable.StopAtBounds

                                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                                delegate: Rectangle {
                                    width: sessionListView.width
                                    height: 44
                                    color: sessionRowMouse.containsMouse
                                        ? "#F3F4F6"
                                        : index % 2 === 0 ? "white" : "#F9FAFB"

                                    Rectangle {
                                        anchors.bottom: parent.bottom
                                        width: parent.width; height: 1; color: "#F3F4F6"
                                    }

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 12
                                        spacing: 0

                                        // #
                                        Label {
                                            Layout.preferredWidth: 36
                                            text: (index + 1).toString()
                                            font.pixelSize: 13; color: "#9CA3AF"
                                            horizontalAlignment: Text.AlignCenter
                                        }

                                        // Product name
                                        Label {
                                            Layout.fillWidth: true
                                            Layout.minimumWidth: 160
                                            text: model.productName || ""
                                            font.pixelSize: 13; font.weight: Font.Medium; color: "#1F2937"
                                            elide: Text.ElideRight
                                        }

                                        // Large unit
                                        Label {
                                            Layout.preferredWidth: 60
                                            text: model.largeUnit || ""
                                            font.pixelSize: 12; color: "#6B7280"
                                            horizontalAlignment: Text.AlignCenter
                                        }

                                        // Conversion
                                        Label {
                                            Layout.preferredWidth: 50
                                            text: model.conversion ? model.conversion.toString() : ""
                                            font.pixelSize: 12; color: "#6B7280"
                                            horizontalAlignment: Text.AlignCenter
                                        }

                                        // Unit price
                                        Label {
                                            Layout.preferredWidth: 80
                                            text: model.unitPrice ? Number(model.unitPrice).toLocaleString('vi-VN') : "0"
                                            font.pixelSize: 12; color: "#6B7280"
                                            horizontalAlignment: Text.AlignRight
                                        }

                                        // Handover qty (editable)
                                        TextField {
                                            Layout.preferredWidth: 100
                                            text: model.handoverQty !== undefined ? model.handoverQty.toString() : "0"
                                            font.pixelSize: 13
                                            horizontalAlignment: Text.AlignCenter
                                            inputMethodHints: Qt.ImhDigitsOnly
                                            selectByMouse: true

                                            background: Rectangle {
                                                radius: 6
                                                color: parent.activeFocus ? "white" : "#F3F4F6"
                                                border.width: parent.activeFocus ? 2 : 1
                                                border.color: parent.activeFocus ? "#10b981" : "#E5E7EB"
                                            }

                                            onEditingFinished: {
                                                calculationVM.updateHandoverQty(index, text)
                                            }
                                        }

                                        // Closing qty (editable)
                                        TextField {
                                            Layout.preferredWidth: 100
                                            text: model.closingQty !== undefined ? model.closingQty.toString() : "0"
                                            font.pixelSize: 13
                                            horizontalAlignment: Text.AlignCenter
                                            inputMethodHints: Qt.ImhDigitsOnly
                                            selectByMouse: true

                                            background: Rectangle {
                                                radius: 6
                                                color: parent.activeFocus ? "white" : "#F3F4F6"
                                                border.width: parent.activeFocus ? 2 : 1
                                                border.color: parent.activeFocus ? "#10b981" : "#E5E7EB"
                                            }

                                            onEditingFinished: {
                                                calculationVM.updateClosingQty(index, text)
                                            }
                                        }

                                        // Used qty (computed)
                                        Label {
                                            Layout.preferredWidth: 60
                                            text: model.usedQty !== undefined ? model.usedQty.toString() : "0"
                                            font.pixelSize: 13; font.weight: Font.Medium
                                            color: model.usedQty > 0 ? "#10B981" : "#9CA3AF"
                                            horizontalAlignment: Text.AlignCenter
                                        }

                                        // Amount (computed)
                                        Label {
                                            Layout.preferredWidth: 100
                                            text: model.amount ? Number(model.amount).toLocaleString('vi-VN') + " đ" : "0 đ"
                                            font.pixelSize: 13; font.weight: Font.Bold
                                            color: model.amount > 0 ? "#047857" : "#9CA3AF"
                                            horizontalAlignment: Text.AlignRight
                                        }
                                    }

                                    MouseArea {
                                        id: sessionRowMouse
                                        anchors.fill: parent
                                        hoverEnabled: true
                                        propagateComposedEvents: true
                                        onPressed: function(mouse) { mouse.accepted = false }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // TAB 1: Product List
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 12

                        Label {
                            text: "📦 Danh sách Sản phẩm"
                            font.pixelSize: 18
                            font.weight: Font.Medium
                            color: "#1F2937"
                        }

                        Item { Layout.fillWidth: true }

                        SearchField {
                            id: productSearchField
                            Layout.preferredWidth: 250
                            placeholderText: "Tìm sản phẩm..."
                        }
                    }

                    ListView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        model: calculationVM.productItems
                        spacing: 4

                        ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                        delegate: Rectangle {
                            width: parent ? parent.width : 0
                            height: 56
                            radius: 8
                            color: prodRowMouse.containsMouse ? "#F3F4F6" : "white"
                            border.width: 1
                            border.color: "#F3F4F6"

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 16
                                anchors.rightMargin: 16
                                spacing: 12

                                // Favorite star
                                Label {
                                    text: model.isFavorite ? "⭐" : "☆"
                                    font.pixelSize: 18
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
                                        font.pixelSize: 14
                                        font.weight: Font.Medium
                                        color: "#1F2937"
                                        elide: Text.ElideRight
                                    }

                                    Label {
                                        text: (model.largeUnit || "") + " × " + (model.conversion || 1)
                                        font.pixelSize: 11
                                        color: "#6B7280"
                                    }
                                }

                                // Price
                                Label {
                                    text: model.unitPrice ? Number(model.unitPrice).toLocaleString('vi-VN') + " đ" : ""
                                    font.pixelSize: 14
                                    font.weight: Font.Bold
                                    color: "#10B981"
                                }

                                // Active indicator
                                Rectangle {
                                    width: 8; height: 8; radius: 4
                                    color: model.isActive ? "#10B981" : "#DC2626"
                                }
                            }

                            MouseArea {
                                id: prodRowMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                propagateComposedEvents: true
                                onPressed: function(mouse) { mouse.accepted = false }
                            }
                        }
                    }
                }
            }
        }
    }

    // ── Dialogs ──
    SaveSessionDialog {
        id: saveSessionDialog
    }

    ConfirmDialog {
        id: resetConfirm
    }

    // Refresh data when tab becomes visible
    Connections {
        target: calculationVM
        function onSessionSaved() {
            globalToast.show("✅ Đã lưu ca thành công!", "success")
        }
        function onSessionReset() {
            globalToast.show("🔄 Đã reset ca", "info")
        }
        function onErrorOccurred(msg) {
            globalToast.show(msg, "error")
        }
    }
}
