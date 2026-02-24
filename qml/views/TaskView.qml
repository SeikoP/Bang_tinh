import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts
import "../components"
import "../dialogs"

/**
 * TaskView — Task/note management with filter chips.
 */
Item {
    id: taskViewRoot

    Component.onCompleted: taskVM.refreshData()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingMd
        spacing: Theme.spacingSm

        // Header
        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "Công việc"
                font: Theme.typography.titleMedium
                color: Theme.backgroundText
            }

            // Pending badge
            Rectangle {
                visible: taskVM.pendingCount > 0
                width: pendingLabel.implicitWidth + 16
                height: 24
                radius: 12
                color: Theme.errorContainer

                Label {
                    id: pendingLabel
                    anchors.centerIn: parent
                    text: taskVM.pendingCount + " chưa xong"
                    font: Theme.typography.labelSmall
                    color: Theme.error
                }
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "+ Thêm"
                Material.background: Theme.primary
                Material.foreground: Theme.surface
                onClicked: {
                    taskDialog.openForNew()
                }
            }
        }

        // Filter chips
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.spacingSm

            Repeater {
                model: [
                    { label: "Tất cả", value: "" },
                    { label: "Chưa thu", value: "unpaid" },
                    { label: "Chưa giao", value: "undelivered" },
                    { label: "Chưa nhận", value: "unreceived" },
                    { label: "Khác", value: "other" }
                ]

                delegate: Rectangle {
                    width: chipLabel.implicitWidth + 24
                    height: 32
                    radius: 16
                    color: taskVM.filterType === modelData.value ? Theme.primary : Theme.surfaceVariant

                    Label {
                        id: chipLabel
                        anchors.centerIn: parent
                        text: modelData.label
                        font: Theme.typography.labelMedium
                        color: taskVM.filterType === modelData.value ? Theme.surface : Theme.textSecondary
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
                height: 68
                radius: Theme.radiusMd
                color: taskItemMouse.containsMouse ? Theme.surfaceVariant : Theme.surface
                border.width: 1
                border.color: model.completed ? Theme.successContainer : Theme.surfaceVariant
                opacity: model.completed ? 0.7 : 1.0

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: Theme.spacingSm

                    // Completion checkbox
                    CheckBox {
                        checked: model.completed || false
                        Material.accent: Theme.primary
                        onToggled: {
                            if (checked) taskVM.markCompleted(model.taskId)
                        }
                    }

                    // Type badge
                    Rectangle {
                        width: typeBadgeLabel.implicitWidth + 12
                        height: 22
                        radius: 4
                        color: Theme.surfaceVariant

                        Label {
                            id: typeBadgeLabel
                            anchors.centerIn: parent
                            text: model.typeDisplay || ""
                            font: Theme.typography.labelSmall
                            color: Theme.textSecondary
                        }
                    }

                    // Task info
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2

                        Label {
                            text: model.description || ""
                            font {
                                family: Theme.typography.labelLarge.family
                                pixelSize: Theme.typography.labelLarge.pixelSize
                                weight: Theme.typography.labelLarge.weight
                                capitalization: Theme.typography.labelLarge.capitalization
                                strikeout: model.completed || false
                            }
                            color: model.completed ? Theme.textDisabled : Theme.backgroundText
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }

                        RowLayout {
                            spacing: 12
                            Label {
                                visible: (model.customerName || "") !== ""
                                text: model.customerName || ""
                                font: Theme.typography.labelSmall
                                color: Theme.surfaceVariantText
                            }
                            Label {
                                visible: model.amount > 0
                                text: model.amount > 0 ? Number(model.amount).toLocaleString('vi-VN') + "đ" : ""
                                font: Theme.typography.labelSmall
                                color: Theme.surfaceVariantText
                            }
                            Label {
                                text: model.createdAt || ""
                                font: Theme.typography.labelSmall
                                color: Theme.textDisabled
                            }
                        }
                    }

                    // Edit
                    Button {
                        text: "Sửa"
                        flat: true
                        font: Theme.typography.labelSmall
                        Material.foreground: Theme.primary
                        visible: !(model.completed || false)
                        onClicked: taskDialog.openForEdit(model.taskId, model.taskType || "", model.description || "", model.customerName || "", model.amount || 0, model.notes || "")
                    }

                    // Delete
                    Button {
                        text: "Xóa"
                        flat: true
                        font: Theme.typography.labelSmall
                        Material.foreground: Theme.error
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
        function onTaskAdded() { globalToast.show("Đã thêm công việc", "success") }
        function onTaskUpdated() { globalToast.show("Đã cập nhật công việc", "success") }
        function onTaskDeleted() { globalToast.show("Đã xóa công việc", "info") }
    }
}
