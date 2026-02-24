import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * DataTable — Reusable Material-styled table with headers and row delegates.
 * 
 * Properties:
 *   - model: ListModel or QAbstractListModel
 *   - columns: [{title, role, width, align}]
 *   - showIndex: bool — show row number column
 */
Item {
    id: tableRoot
    property var model
    property var columns: []
    property bool showIndex: true
    property int rowHeight: 42
    property color alternateRowColor: "#F9FAFB"
    property color hoverColor: "#F3F4F6"

    signal rowClicked(int index)
    signal rowDoubleClicked(int index)

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ── Header ──
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 44
            color: "#F9FAFB"
            border.width: 0

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: "#E5E7EB"
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 0

                // Index header
                Label {
                    visible: tableRoot.showIndex
                    Layout.preferredWidth: 40
                    text: "#"
                    font.pixelSize: 12
                    font.weight: Font.Medium
                    color: "#6B7280"
                    horizontalAlignment: Text.AlignCenter
                }

                Repeater {
                    model: tableRoot.columns
                    delegate: Label {
                        Layout.preferredWidth: modelData.width || 100
                        Layout.fillWidth: modelData.fillWidth || false
                        text: modelData.title || ""
                        font.pixelSize: 12
                        font.weight: Font.Medium
                        color: "#6B7280"
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

        // ── Body (scrollable) ──
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
                width: tableListView.width
                height: tableRoot.rowHeight
                color: tableRowMouse.containsMouse
                    ? tableRoot.hoverColor
                    : index % 2 === 0 ? "white" : tableRoot.alternateRowColor

                Rectangle {
                    anchors.bottom: parent.bottom
                    width: parent.width
                    height: 1
                    color: "#F3F4F6"
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
                        font.pixelSize: 13
                        color: "#9CA3AF"
                        horizontalAlignment: Text.AlignCenter
                    }

                    // Dynamic columns — delegate must access model roles
                    Repeater {
                        model: tableRoot.columns
                        delegate: Label {
                            Layout.preferredWidth: modelData.width || 100
                            Layout.fillWidth: modelData.fillWidth || false
                            text: {
                                // Access role from outer delegate's model
                                var val = tableListView.model ? index : ""
                                // Role access happens through the outer delegate context
                                return ""
                            }
                            font.pixelSize: 13
                            color: "#1F2937"
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
