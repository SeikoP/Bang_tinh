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
    title: "📦 Quản lý Kho hàng"

    // Material Dark theme with Emerald accent
    Material.theme: Material.Light
    Material.accent: "#10b981"
    Material.primary: "#10b981"
    Material.background: "#FFFFFF"
    Material.foreground: "#1F2937"

    // ─── Global toast overlay ───
    NotificationToast {
        id: globalToast
        z: 999
    }

    // Connect to appVM signals
    Connections {
        target: appVM
        function onToastRequested(message, type) {
            globalToast.show(message, type)
        }
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
            Layout.preferredWidth: 72
            color: "#0f172a"  // Slate-900

            ColumnLayout {
                anchors.fill: parent
                anchors.topMargin: 16
                anchors.bottomMargin: 16
                spacing: 4

                // Logo
                Label {
                    Layout.alignment: Qt.AlignHCenter
                    text: "📦"
                    font.pixelSize: 28
                    Layout.bottomMargin: 16
                }

                // Navigation items
                Repeater {
                    model: [
                        { icon: "📊", label: "Quản lý", index: 0 },
                        { icon: "📋", label: "Công việc", index: 1 },
                        { icon: "💰", label: "Ngân hàng", index: 2 },
                        { icon: "📜", label: "Lịch sử", index: 3 },
                        { icon: "⚙️", label: "Cài đặt", index: 4 },
                        { icon: "🔢", label: "Máy tính", index: 5 }
                    ]

                    delegate: Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 64
                        Layout.leftMargin: 8
                        Layout.rightMargin: 8
                        radius: 12
                        color: appVM.currentView === modelData.index
                            ? Qt.rgba(0.063, 0.725, 0.506, 0.15)  // primary/15%
                            : navMouseArea.containsMouse
                                ? "#1e293b"  // Slate-800
                                : "transparent"

                        ColumnLayout {
                            anchors.centerIn: parent
                            spacing: 4

                            Label {
                                Layout.alignment: Qt.AlignHCenter
                                text: modelData.icon
                                font.pixelSize: 22
                            }

                            Label {
                                Layout.alignment: Qt.AlignHCenter
                                text: modelData.label
                                font.pixelSize: 10
                                font.weight: Font.Medium
                                color: appVM.currentView === modelData.index
                                    ? "#10b981"
                                    : "#94a3b8"
                            }
                        }

                        MouseArea {
                            id: navMouseArea
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onClicked: appVM.switchView(modelData.index)
                        }

                        // Active indicator bar
                        Rectangle {
                            visible: appVM.currentView === modelData.index
                            width: 3
                            height: 32
                            radius: 2
                            color: "#10b981"
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
                    font.pixelSize: 9
                    color: "#64748b"
                    Layout.topMargin: 8
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
                Layout.preferredHeight: 64
                color: "#FFFFFF"

                // Bottom border
                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 1
                    color: "#E5E7EB"
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 24
                    anchors.rightMargin: 24

                    // Breadcrumb
                    Label {
                        text: {
                            var titles = ["📊 Quản lý", "📋 Công việc", "💰 Ngân hàng", "📜 Lịch sử", "⚙️ Cài đặt", "🔢 Máy tính"]
                            return titles[appVM.currentView] || ""
                        }
                        font.pixelSize: 20
                        font.weight: Font.Medium
                        color: "#1F2937"
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
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: appVM.currentView

                // 0: Management (Calculation + Stock + Product tabs)
                CalculationView { }

                // 1: Tasks
                TaskView { }

                // 2: Bank
                BankView { }

                // 3: History
                HistoryView { }

                // 4: Settings
                SettingsView { }

                // 5: Calculator Tool
                CalculatorToolView { }
            }
        }
    }

    // ─── Keyboard shortcuts ───
    Shortcut {
        sequence: "Ctrl+1"
        onActivated: appVM.switchView(0)
    }
    Shortcut {
        sequence: "Ctrl+2"
        onActivated: appVM.switchView(1)
    }
    Shortcut {
        sequence: "Ctrl+3"
        onActivated: appVM.switchView(2)
    }
    Shortcut {
        sequence: "Ctrl+4"
        onActivated: appVM.switchView(3)
    }
    Shortcut {
        sequence: "Ctrl+5"
        onActivated: appVM.switchView(4)
    }
    Shortcut {
        sequence: "Ctrl+6"
        onActivated: appVM.switchView(5)
    }

    Component.onCompleted: {
        appVM.startServices()
        calculationVM.refreshData()
    }
}
