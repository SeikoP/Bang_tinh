import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * Main Application Window
 * Material 3 layout: NavigationRail (left) + ToolBar (top) + StackLayout (center)
 */
ApplicationWindow {
    id: root
    visible: true
    width: 1280
    height: 800
    minimumWidth: 960
    minimumHeight: 600
    title: "Quản lý Kho hàng"

    Material.theme: Material.Light
    Material.accent: Theme.primary
    Material.primary: Theme.primary
    Material.background: Theme.background
    Material.foreground: Theme.backgroundText

    // ─── Global toast overlay ───
    NotificationToast {
        id: globalToast
        z: 999
    }

    // ─── QuickBankPeek popup ───
    QuickBankPeek {
        id: bankPeek
    }

    // Connect to appVM signals
    Connections {
        target: appVM
        function onToastRequested(message, type) {
            globalToast.show(message, type)
        }
        function onBankNotificationReceived(message) {
            headerBanner.show(message, "bank")
        }
    }

    // ─── View fade transition helper ───
    property int _prevView: 0

    Connections {
        target: appVM
        function onCurrentViewChanged() {
            contentFadeOut.start()
        }
    }

    NumberAnimation {
        id: contentFadeOut
        target: contentStack
        property: "opacity"
        from: 1; to: 0
        duration: Theme.animFast
        easing.type: Easing.InCubic
        onFinished: contentFadeIn.start()
    }

    NumberAnimation {
        id: contentFadeIn
        target: contentStack
        property: "opacity"
        from: 0; to: 1
        duration: Theme.animFast
        easing.type: Easing.OutCubic
    }

    // ─── Main layout: sidebar + content ───
    RowLayout {
        anchors.fill: parent
        spacing: 0

        // ════════════════════════════════════
        // Navigation Rail (Sidebar)
        // ════════════════════════════════════
        Rectangle {
            id: navRail
            Layout.fillHeight: true
            Layout.preferredWidth: Theme.sidebarWidth
            color: Theme.sidebarBg

            ColumnLayout {
                anchors.fill: parent
                anchors.topMargin: Theme.spacingMd
                anchors.bottomMargin: Theme.spacingMd
                spacing: Theme.spacingXs

                // App title
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: "KHO"
                    font.pixelSize: 16
                    font.weight: Font.Bold
                    font.letterSpacing: 2
                    color: Theme.primary
                    Layout.bottomMargin: Theme.spacingMd
                }

                // Navigation items
                Repeater {
                    model: [
                        { label: "Quản lý", index: 0 },
                        { label: "Công việc", index: 1 },
                        { label: "Ngân hàng", index: 2 },
                        { label: "Lịch sử", index: 3 },
                        { label: "Cài đặt", index: 4 },
                        { label: "Máy tính", index: 5 }
                    ]

                    delegate: Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 52
                        Layout.leftMargin: Theme.spacingSm
                        Layout.rightMargin: Theme.spacingSm
                        radius: Theme.radiusLg
                        color: appVM.currentView === modelData.index
                            ? Theme.withAlpha(Theme.primary, 0.15)
                            : navMouseArea.containsMouse
                                ? Theme.sidebarItemHover
                                : "transparent"

                        Label {
                            anchors.centerIn: parent
                            text: modelData.label
                            font: Theme.typography.labelMedium
                            color: appVM.currentView === modelData.index
                                ? Theme.sidebarItemActive
                                : Theme.sidebarText
                        }

                        MouseArea {
                            id: navMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: appVM.switchView(modelData.index)
                            // Long-press on Bank nav to open peek
                            onPressAndHold: {
                                if (modelData.index === 2) {
                                    bankPeek.x = navRail.width + 8
                                    bankPeek.y = parent.mapToItem(root.contentItem, 0, 0).y
                                    bankPeek.open()
                                }
                            }
                        }

                        // Active indicator bar
                        Rectangle {
                            visible: appVM.currentView === modelData.index
                            width: 3
                            height: 24
                            radius: 2
                            color: Theme.primary
                            anchors.left: parent.left
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                // Server status indicator
                StatusIndicator {
                    Layout.alignment: Qt.AlignHCenter
                    status: appVM.serverStatus
                }

                // Version label
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: appVM.appVersion
                    font: Theme.typography.labelSmall
                    color: Theme.textTertiary
                    Layout.topMargin: Theme.spacingSm
                }
            }
        }

        // ════════════════════════════════════
        // Main Content Area
        // ════════════════════════════════════
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            // ── Header / Toolbar ──
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: Theme.headerHeight
                color: Theme.surface

                // Bottom border
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 1
                    color: Theme.outline
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Theme.spacingLg
                    anchors.rightMargin: Theme.spacingLg

                    // Breadcrumb
                    Label {
                        text: {
                            var titles = ["Quản lý", "Công việc", "Ngân hàng", "Lịch sử", "Cài đặt", "Máy tính"]
                            return titles[appVM.currentView] || ""
                        }
                        font: Theme.typography.titleLarge
                        color: Theme.backgroundText
                    }

                    Item { Layout.fillWidth: true }

                    // Notification banner area
                    NotificationBanner {
                        id: headerBanner
                    }
                }
            }

            // ── Content Stack ──
            StackLayout {
                id: contentStack
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: appVM.currentView

                CalculationView { }
                TaskView { }
                BankView { }
                HistoryView { }
                SettingsView { }
                CalculatorToolView { }
            }
        }
    }

    // ─── Keyboard shortcuts ───
    Shortcut { sequence: "Ctrl+1"; onActivated: appVM.switchView(0) }
    Shortcut { sequence: "Ctrl+2"; onActivated: appVM.switchView(1) }
    Shortcut { sequence: "Ctrl+3"; onActivated: appVM.switchView(2) }
    Shortcut { sequence: "Ctrl+4"; onActivated: appVM.switchView(3) }
    Shortcut { sequence: "Ctrl+5"; onActivated: appVM.switchView(4) }
    Shortcut { sequence: "Ctrl+6"; onActivated: appVM.switchView(5) }
    Shortcut { sequence: "Ctrl+S"; onActivated: settingsVM.createBackup() }
    Shortcut { sequence: "F5"; onActivated: calculationVM.refreshData() }
    Shortcut { sequence: "Ctrl+Q"; onActivated: Qt.quit() }
    Shortcut { sequence: "Escape"; onActivated: headerBanner.hide() }

    Component.onCompleted: {
        appVM.startServices()
        calculationVM.refreshData()
    }
}
