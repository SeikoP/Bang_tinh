import QtQuick
import QtQuick.Controls.Material

/**
 * StatusIndicator — Server connection status dot.
 * property status: "connected" | "disconnected" | "connecting"
 */
Item {
    id: statusRoot
    width: 48
    height: 48

    property string status: "disconnected"

    Column {
        anchors.centerIn: parent
        spacing: 4

        // Status dot
        Rectangle {
            id: dot
            width: 10
            height: 10
            radius: 5
            anchors.horizontalCenter: parent.horizontalCenter
            color: {
                if (statusRoot.status === "connected") return Theme.success
                if (statusRoot.status === "connecting") return Theme.warningColor
                return Theme.error
            }

            // Pulsing animation when connecting
            SequentialAnimation on opacity {
                running: statusRoot.status === "connecting"
                loops: Animation.Infinite
                NumberAnimation { from: 1; to: 0.3; duration: 600 }
                NumberAnimation { from: 0.3; to: 1; duration: 600 }
            }
        }

        // Label
        Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: {
                if (statusRoot.status === "connected") return "Online"
                if (statusRoot.status === "connecting") return "..."
                return "Offline"
            }
            font: Theme.typography.labelSmall
            color: Theme.textTertiary
        }
    }

    // Tooltip
    ToolTip {
        visible: hoverArea.containsMouse
        text: {
            if (statusRoot.status === "connected") return "Server đang hoạt động"
            if (statusRoot.status === "connecting") return "Đang kết nối..."
            return "Server offline"
        }
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
    }
}
