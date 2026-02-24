import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * NotificationToast — Material 3 snackbar-style popup
 * Call show(message, type) from anywhere. Auto-dismisses after 4 seconds.
 * Types: "success", "error", "warning", "info"
 */
Item {
    id: toastRoot
    anchors.bottom: parent ? parent.bottom : undefined
    anchors.horizontalCenter: parent ? parent.horizontalCenter : undefined
    anchors.bottomMargin: Theme.spacingXl
    width: toastContent.width
    height: toastContent.height
    opacity: 0
    visible: opacity > 0
    z: 999

    function show(message, type) {
        toastLabel.text = message
        var colors = {
            "success": Theme.success,
            "error": Theme.error,
            "warning": Theme.warningColor,
            "info": Theme.info
        }
        toastBg.color = colors[type] || colors["info"]
        showAnim.start()
        hideTimer.restart()
    }

    Timer {
        id: hideTimer
        interval: 4000
        onTriggered: hideAnim.start()
    }

    NumberAnimation {
        id: showAnim
        target: toastRoot
        property: "opacity"
        from: 0; to: 1
        duration: Theme.animNormal
        easing.type: Easing.OutCubic
    }

    NumberAnimation {
        id: hideAnim
        target: toastRoot
        property: "opacity"
        from: 1; to: 0
        duration: Theme.animNormal
        easing.type: Easing.InCubic
    }

    Rectangle {
        id: toastContent
        width: toastRow.width + 32
        height: toastRow.height + 20
        radius: Theme.radiusLg
        color: "transparent"

        Rectangle {
            id: toastBg
            anchors.fill: parent
            radius: parent.radius
            color: Theme.info
            opacity: 0.95
        }

        layer.enabled: true
        layer.effect: null

        RowLayout {
            id: toastRow
            anchors.centerIn: parent
            spacing: Theme.spacingSm

            Label {
                id: toastLabel
                text: ""
                font: Theme.typography.labelLarge
                color: Theme.primaryText
                maximumLineCount: 2
                wrapMode: Text.WordWrap
                Layout.maximumWidth: 400
            }

            Label {
                text: "×"
                font.pixelSize: 16
                font.weight: Font.Medium
                color: Qt.rgba(1, 1, 1, 0.7)
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -4
                    cursorShape: Qt.PointingHandCursor
                    onClicked: hideAnim.start()
                }
            }
        }
    }
}
