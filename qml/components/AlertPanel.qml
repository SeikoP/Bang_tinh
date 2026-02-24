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
        NumberAnimation { duration: Theme.animFast; easing.type: Easing.OutCubic }
    }

    ScrollView {
        anchors.fill: parent
        clip: true

        ColumnLayout {
            id: alertColumn
            width: parent.width
            spacing: Theme.spacingXs

            Repeater {
                model: alertRoot.alerts

                delegate: Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 36
                    radius: Theme.radiusMd
                    color: {
                        if (modelData.type === "warning") return Theme.warningContainer
                        if (modelData.type === "error") return Theme.errorContainer
                        return Theme.infoContainer
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 12
                        anchors.rightMargin: 12
                        spacing: Theme.spacingSm

                        Rectangle {
                            width: 6
                            height: 6
                            radius: 3
                            color: {
                                if (modelData.type === "warning") return Theme.warningColor
                                if (modelData.type === "error") return Theme.error
                                return Theme.info
                            }
                        }

                        Label {
                            Layout.fillWidth: true
                            text: modelData.message || ""
                            font: Theme.typography.bodySmall
                            color: Theme.backgroundText
                            elide: Text.ElideRight
                        }
                    }
                }
            }
        }
    }
}
