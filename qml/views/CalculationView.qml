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

        // Tab Bar
        TabBar {
            id: calcTabBar
            Layout.fillWidth: true
            Material.accent: Theme.primary

            TabButton {
                text: "Tính tiền"
                font: Theme.typography.labelLarge
                width: implicitWidth
            }

            TabButton {
                text: "Danh sách Sản phẩm"
                font: Theme.typography.labelLarge
                width: implicitWidth
            }
        }

        // Tab Content
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: calcTabBar.currentIndex

            // ━━━ TAB 0: Calculation Table ━━━
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Theme.spacingMd
                    spacing: Theme.spacingSm

                    // Alert panel (wired when VM exposes alerts)
                    AlertPanel {
                        id: calcAlerts
                        Layout.fillWidth: true
                        alerts: calculationVM.alerts || []
                    }

                    // Header row with total
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.spacingMd

                        Label {
                            text: "Bảng tính ca"
                            font: Theme.typography.titleMedium
                            color: Theme.backgroundText
                        }

                        Item { Layout.fillWidth: true }

                        // Total amount card
                        Rectangle {
                            Layout.preferredWidth: totalLabel.implicitWidth + 40
                            Layout.preferredHeight: 44
                            radius: Theme.radiusLg
                            color: Theme.withAlpha(Theme.primary, 0.1)
                            border.width: 1
                            border.color: Theme.withAlpha(Theme.primary, 0.3)

                            RowLayout {
                                anchors.centerIn: parent
                                spacing: Theme.spacingSm

                                Label {
                                    text: "Tổng:"
                                    font: Theme.typography.bodyMedium
                                    color: Theme.primaryDark
                                }

                                Label {
                                    id: totalLabel
                                    text: calculationVM.formatTotal() + " đ"
                                    font: Theme.typography.titleMedium
                                    color: Theme.primaryDark
                                }
                            }
                        }

                        // Action buttons
                        Button {
                            text: "Lưu ca"
                            Material.background: Theme.primary
                            Material.foreground: Theme.primaryText
                            font: Theme.typography.labelLarge
                            onClicked: saveSessionDialog.open()
                        }

                        Button {
                            text: "Reset"
                            Material.background: Theme.surfaceVariant
                            Material.foreground: Theme.textSecondary
                            font: Theme.typography.labelLarge
                            onClicked: resetConfirm.show(
                                "Reset ca?",
                                "Đặt lại tất cả số lượng về 0. Thao tác này không thể hoàn tác.",
                                function() { calculationVM.resetSession() }
                            )
                        }
                    }

                    // Session Table
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: Theme.radiusLg
                        border.width: 1
                        border.color: Theme.outline
                        clip: true

                        ColumnLayout {
                            anchors.fill: parent
                            spacing: 0

                            // Table Header
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 44
                                color: Theme.backgroundSecondary

                                Rectangle {
                                    anchors.bottom: parent.bottom
                                    width: parent.width; height: 1; color: Theme.outline
                                }

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12
                                    spacing: 0

                                    Label { Layout.preferredWidth: 36; text: "#"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.fillWidth: true; Layout.minimumWidth: 160; text: "Sản phẩm"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText }
                                    Label { Layout.preferredWidth: 60; text: "ĐV lớn"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 50; text: "Quy đổi"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 80; text: "Đơn giá"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; horizontalAlignment: Text.AlignRight }
                                    Label { Layout.preferredWidth: 100; text: "SL Giao"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 100; text: "SL Đóng"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 60; text: "Đã dùng"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; horizontalAlignment: Text.AlignCenter }
                                    Label { Layout.preferredWidth: 100; text: "Thành tiền"; font: Theme.typography.labelMedium; color: Theme.surfaceVariantText; horizontalAlignment: Text.AlignRight }
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
                                        ? Theme.surfaceVariant
                                        : index % 2 === 0 ? Theme.surface : Theme.backgroundSecondary

                                    Rectangle {
                                        anchors.bottom: parent.bottom
                                        width: parent.width; height: 1; color: Theme.divider
                                    }

                                    RowLayout {
                                        anchors.fill: parent
                                        anchors.leftMargin: 12
                                        anchors.rightMargin: 12
                                        spacing: 0

                                        Label {
                                            Layout.preferredWidth: 36
                                            text: (index + 1).toString()
                                            font: Theme.typography.bodyMedium; color: Theme.textDisabled
                                            horizontalAlignment: Text.AlignCenter
                                        }

                                        Label {
                                            Layout.fillWidth: true
                                            Layout.minimumWidth: 160
                                            text: model.productName || ""
                                            font: Theme.typography.labelLarge; color: Theme.backgroundText
                                            elide: Text.ElideRight
                                        }

                                        Label {
                                            Layout.preferredWidth: 60
                                            text: model.largeUnit || ""
                                            font: Theme.typography.bodySmall; color: Theme.surfaceVariantText
                                            horizontalAlignment: Text.AlignCenter
                                        }

                                        Label {
                                            Layout.preferredWidth: 50
                                            text: model.conversion ? model.conversion.toString() : ""
                                            font: Theme.typography.bodySmall; color: Theme.surfaceVariantText
                                            horizontalAlignment: Text.AlignCenter
                                        }

                                        Label {
                                            Layout.preferredWidth: 80
                                            text: model.unitPrice ? Number(model.unitPrice).toLocaleString('vi-VN') : "0"
                                            font: Theme.typography.bodySmall; color: Theme.surfaceVariantText
                                            horizontalAlignment: Text.AlignRight
                                        }

                                        // Handover qty (editable)
                                        TextField {
                                            Layout.preferredWidth: 100
                                            text: model.handoverQty !== undefined ? model.handoverQty.toString() : "0"
                                            font: Theme.typography.bodyMedium
                                            horizontalAlignment: Text.AlignCenter
                                            inputMethodHints: Qt.ImhDigitsOnly
                                            selectByMouse: true

                                            background: Rectangle {
                                                radius: Theme.radiusSm
                                                color: parent.activeFocus ? Theme.surface : Theme.surfaceVariant
                                                border.width: parent.activeFocus ? 2 : 1
                                                border.color: parent.activeFocus ? Theme.primary : Theme.outline
                                            }

                                            onEditingFinished: {
                                                calculationVM.updateHandoverQty(index, text)
                                            }
                                        }

                                        // Closing qty (editable)
                                        TextField {
                                            Layout.preferredWidth: 100
                                            text: model.closingQty !== undefined ? model.closingQty.toString() : "0"
                                            font: Theme.typography.bodyMedium
                                            horizontalAlignment: Text.AlignCenter
                                            inputMethodHints: Qt.ImhDigitsOnly
                                            selectByMouse: true

                                            background: Rectangle {
                                                radius: Theme.radiusSm
                                                color: parent.activeFocus ? Theme.surface : Theme.surfaceVariant
                                                border.width: parent.activeFocus ? 2 : 1
                                                border.color: parent.activeFocus ? Theme.primary : Theme.outline
                                            }

                                            onEditingFinished: {
                                                calculationVM.updateClosingQty(index, text)
                                            }
                                        }

                                        // Used qty (computed)
                                        Label {
                                            Layout.preferredWidth: 60
                                            text: model.usedQty !== undefined ? model.usedQty.toString() : "0"
                                            font: Theme.typography.labelLarge
                                            color: model.usedQty > 0 ? Theme.primary : Theme.textDisabled
                                            horizontalAlignment: Text.AlignCenter
                                        }

                                        // Amount (computed)
                                        Label {
                                            Layout.preferredWidth: 100
                                            text: model.amount ? Number(model.amount).toLocaleString('vi-VN') + " đ" : "0 đ"
                                            font.pixelSize: 13; font.weight: Font.Bold
                                            color: model.amount > 0 ? Theme.primaryDark : Theme.textDisabled
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

            // ━━━ TAB 1: Product List ━━━
            Item {
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: Theme.spacingMd
                    spacing: Theme.spacingSm

                    RowLayout {
                        Layout.fillWidth: true
                        spacing: Theme.spacingSm

                        Label {
                            text: "Danh sách Sản phẩm"
                            font: Theme.typography.titleMedium
                            color: Theme.backgroundText
                        }

                        Item { Layout.fillWidth: true }

                        SearchField {
                            id: productSearchField
                            Layout.preferredWidth: 250
                            placeholderText: "Tìm sản phẩm..."
                            onTextChanged: calculationVM.filterProducts(text)
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
                            radius: Theme.radiusMd
                            color: prodRowMouse.containsMouse ? Theme.surfaceVariant : Theme.surface
                            border.width: 1
                            border.color: Theme.divider

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: Theme.spacingMd
                                anchors.rightMargin: Theme.spacingMd
                                spacing: Theme.spacingSm

                                // Favorite toggle
                                Rectangle {
                                    width: 28; height: 28; radius: 14
                                    color: model.isFavorite ? Theme.withAlpha(Theme.warningColor, 0.15) : Theme.surfaceVariant

                                    Label {
                                        anchors.centerIn: parent
                                        text: model.isFavorite ? "★" : "☆"
                                        font.pixelSize: 14
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
                                        elide: Text.ElideRight
                                    }

                                    Label {
                                        text: (model.largeUnit || "") + " × " + (model.conversion || 1)
                                        font: Theme.typography.labelSmall
                                        color: Theme.surfaceVariantText
                                    }
                                }

                                // Price
                                Label {
                                    text: model.unitPrice ? Number(model.unitPrice).toLocaleString('vi-VN') + " đ" : ""
                                    font: Theme.typography.labelLarge
                                    color: Theme.primary
                                }

                                // Active indicator
                                Rectangle {
                                    width: 8; height: 8; radius: 4
                                    color: model.isActive ? Theme.success : Theme.error
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

    // Dialogs
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
            globalToast.show("Đã lưu ca thành công!", "success")
        }
        function onSessionReset() {
            globalToast.show("Đã reset ca", "info")
        }
        function onErrorOccurred(msg) {
            globalToast.show(msg, "error")
        }
    }
}
