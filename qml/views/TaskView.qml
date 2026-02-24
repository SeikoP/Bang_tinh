import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * TaskView — Task/note management with filter chips.
 */
Item {
    id: taskViewRoot

    Component.onCompleted: taskVM.refreshData()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        // Header
        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "📋 Công việc"
                font.pixelSize: 18
                font.weight: Font.Medium
                color: "#1F2937"
            }

            // Pending badge
            Rectangle {
                visible: taskVM.pendingCount > 0
                width: pendingLabel.implicitWidth + 16
                height: 24
                radius: 12
                color: "#fee2e2"

                Label {
                    id: pendingLabel
                    anchors.centerIn: parent
                    text: taskVM.pendingCount + " chưa xong"
                    font.pixelSize: 11
                    font.weight: Font.Medium
                    color: "#DC2626"
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "+ Thêm"
                Material.background: "#10b981"
                Material.foreground: "white"
                onClicked: {
                    taskDialog.clear()
                    taskDialog.open()
                }
            }
        }

        // Filter chips
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Repeater {
                model: [
                    { label: "Tất cả", value: "" },
                    { label: "💵 Chưa thu", value: "unpaid" },
                    { label: "📦 Chưa giao", value: "undelivered" },
                    { label: "📥 Chưa nhận", value: "unreceived" },
                    { label: "🗂️ Khác", value: "other" }
                ]

                delegate: Rectangle {
                    width: chipLabel.implicitWidth + 24
                    height: 32
                    radius: 16
                    color: taskVM.filterType === modelData.value ? "#10b981" : "#F3F4F6"

                    Label {
                        id: chipLabel
                        anchors.centerIn: parent
                        text: modelData.label
                        font.pixelSize: 12
                        font.weight: Font.Medium
                        color: taskVM.filterType === modelData.value ? "white" : "#374151"
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: taskVM.filterType = modelData.value
                    }
                }
            }
        }

        // Task list
        ListView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: taskVM.tasks
            spacing: 6

            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                width: parent ? parent.width : 0
                height: 64
                radius: 10
                color: taskItemMouse.containsMouse ? "#F3F4F6" : "white"
                border.width: 1
                border.color: model.completed ? "#d1fae5" : "#F3F4F6"
                opacity: model.completed ? 0.7 : 1.0

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 12

                    // Completion checkbox
                    CheckBox {
                        checked: model.completed || false
                        Material.accent: "#10b981"
                        onToggled: {
                            if (checked) taskVM.markCompleted(model.taskId)
                        }
                    }

                    // Type badge
                    Label {
                        text: model.typeDisplay || ""
                        font.pixelSize: 13
                    }

                    // Task info
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: model.description || ""
                            font.pixelSize: 14
                            font.weight: Font.Medium
                            color: model.completed ? "#9CA3AF" : "#1F2937"
                            font.strikeout: model.completed || false
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        RowLayout {
                            spacing: 12
                            Label {
                                visible: (model.customerName || "") !== ""
                                text: "👤 " + (model.customerName || "")
                                font.pixelSize: 11; color: "#6B7280"
                            }
                            Label {
                                visible: model.amount > 0
                                text: "💰 " + (model.amount > 0 ? Number(model.amount).toLocaleString('vi-VN') + "đ" : "")
                                font.pixelSize: 11; color: "#6B7280"
                            }
                            Label {
                                text: model.createdAt || ""
                                font.pixelSize: 10; color: "#9CA3AF"
                            }
                        }
                    }

                    // Delete
                    RoundButton {
                        text: "🗑️"
                        width: 32; height: 32
                        flat: true
                        onClicked: taskVM.deleteTask(model.taskId)
                    }
                }

                MouseArea {
                    id: taskItemMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    propagateComposedEvents: true
                    onPressed: function(mouse) { mouse.accepted = false }
                }
            }
        }
    }

    TaskDialog { id: taskDialog }

    Connections {
        target: taskVM
        function onTaskAdded() { globalToast.show("✅ Đã thêm công việc!", "success") }
        function onTaskDeleted() { globalToast.show("🗑️ Đã xóa công việc", "info") }
    }
}
