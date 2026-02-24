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
    anchors.bottomMargin: 32
    width: toastContent.width
    height: toastContent.height
    opacity: 0
    visible: opacity > 0
    z: 999

    function show(message, type) {
        toastLabel.text = message
        var colors = {
            "success": "#10B981",
            "error": "#DC2626",
            "warning": "#F59E0B",
            "info": "#2563EB"
        }
        var icons = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        toastBg.color = colors[type] || colors["info"]
        toastIcon.text = icons[type] || icons["info"]
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
        duration: 250
        easing.type: Easing.OutCubic
    }

    NumberAnimation {
        id: hideAnim
        target: toastRoot
        property: "opacity"
        from: 1; to: 0
        duration: 250
        easing.type: Easing.InCubic
    }

    Rectangle {
        id: toastContent
        width: toastRow.width + 32
        height: toastRow.height + 20
        radius: 12
        color: "transparent"

        Rectangle {
            id: toastBg
            anchors.fill: parent
            radius: parent.radius
            color: "#10B981"
            opacity: 0.95
        }

        // Shadow
        layer.enabled: true
        layer.effect: null

        RowLayout {
            id: toastRow
            anchors.centerIn: parent
            spacing: 10

            Label {
                id: toastIcon
                text: "✅"
                font.pixelSize: 18
                color: "white"
            }

            Label {
                id: toastLabel
                text: ""
                font.pixelSize: 14
                font.weight: Font.Medium
                color: "white"
                maximumLineCount: 2
                wrapMode: Text.WordWrap
                Layout.maximumWidth: 400
            }

            // Close button
            Label {
                text: "✕"
                font.pixelSize: 14
                color: Qt.rgba(1, 1, 1, 0.7)
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: hideAnim.start()
                }
            }
        }
    }
}
