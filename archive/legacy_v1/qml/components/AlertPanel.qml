import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * AlertPanel — Scrollable list of inventory alerts.
 * Binds to alertVM/appVM alerts.
 */
Item {
    id: alertRoot
    property var alerts: []  // [{message, type}]
    visible: alerts.length > 0

    implicitHeight: visible ? Math.min(alertColumn.implicitHeight, 200) : 0

    Behavior on implicitHeight {
        NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
    }

    ScrollView {
        anchors.fill: parent
        clip: true

        ColumnLayout {
            id: alertColumn
            width: parent.width
            spacing: 4

            Repeater {
                model: alertRoot.alerts

                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    radius: 8
                    color: {
                        if (modelData.type === "warning") return "#fef3c7"
                        if (modelData.type === "error") return "#fee2e2"
                        return "#dbeafe"
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: 8

                        Label {
                            text: {
                                if (modelData.type === "warning") return "⚠️"
                                if (modelData.type === "error") return "❌"
                                return "ℹ️"
                            }
                            font.pixelSize: 14
                        }

                        Label {
                            Layout.fillWidth: true
                            text: modelData.message || ""
                            font.pixelSize: 12
                            color: "#1F2937"
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }
    }
}
