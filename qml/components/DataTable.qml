import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * DataTable — Reusable Material-styled table with headers and row delegates.
 *
 * Properties:
 *   - model: ListModel or QAbstractListModel
 *   - columns: [{title, role, width, align, fillWidth}]
 *   - showIndex: bool — show row number column
 */
Item {
    id: tableRoot
    property var model
    property var columns: []
    property bool showIndex: true
    property int rowHeight: 42

    signal rowClicked(int index)
    signal rowDoubleClicked(int index)

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Header
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            color: Theme.backgroundSecondary

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: Theme.outline
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 0

                Label {
                    visible: tableRoot.showIndex
                    Layout.preferredWidth: 40
                    text: "#"
                    font: Theme.typography.labelMedium
                    color: Theme.surfaceVariantText
                    horizontalAlignment: Text.AlignCenter
                }

                Repeater {
                    model: tableRoot.columns
                    delegate: Label {
                        Layout.preferredWidth: modelData.width || 100
                        Layout.fillWidth: modelData.fillWidth || false
                        text: modelData.title || ""
                        font: Theme.typography.labelMedium
                        color: Theme.surfaceVariantText
                        horizontalAlignment: modelData.align === "right"
                            ? Text.AlignRight
                            : modelData.align === "center"
                                ? Text.AlignHCenter
                                : Text.AlignLeft
                        elide: Text.ElideRight
                    }
                }
            }
        }

        // Body (scrollable)
        ListView {
            id: tableListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: tableRoot.model
            boundsBehavior: Flickable.StopAtBounds

            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AsNeeded
            }

            delegate: Rectangle {
                id: rowDelegate
                width: tableListView.width
                height: tableRoot.rowHeight
                color: tableRowMouse.containsMouse
                    ? Theme.surfaceVariant
                    : index % 2 === 0 ? Theme.surface : Theme.backgroundSecondary

                // Store model data for access by inner Repeater
                property var rowModel: model

                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 1
                    color: Theme.divider
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 0

                    // Index column
                    Label {
                        visible: tableRoot.showIndex
                        Layout.preferredWidth: 40
                        text: (index + 1).toString()
                        font: Theme.typography.bodyMedium
                        color: Theme.textDisabled
                        horizontalAlignment: Text.AlignCenter
                    }

                    // Dynamic columns — access role from outer delegate
                    Repeater {
                        model: tableRoot.columns
                        delegate: Label {
                            Layout.preferredWidth: modelData.width || 100
                            Layout.fillWidth: modelData.fillWidth || false
                            text: {
                                var role = modelData.role || ""
                                if (role && rowDelegate.rowModel)
                                    return rowDelegate.rowModel[role] !== undefined
                                        ? rowDelegate.rowModel[role].toString() : ""
                                return ""
                            }
                            font: Theme.typography.bodyMedium
                            color: Theme.backgroundText
                            elide: Text.ElideRight
                            horizontalAlignment: modelData.align === "right"
                                ? Text.AlignRight
                                : modelData.align === "center"
                                    ? Text.AlignHCenter
                                    : Text.AlignLeft
                        }
                    }
                }

                MouseArea {
                    id: tableRowMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: tableRoot.rowClicked(index)
                    onDoubleClicked: tableRoot.rowDoubleClicked(index)
                }
            }
        }
    }
}
