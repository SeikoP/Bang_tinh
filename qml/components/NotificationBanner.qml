import QtQuick
import QtQuick.Controls.Material
import QtQuick.Layouts

/**
 * NotificationBanner — Slide-in banner for header area
 * Shows bank notifications or system alerts.
 */
Item {
    id: bannerRoot
    Layout.fillWidth: true
    height: visible ? 40 : 0
    visible: bannerText.text !== ""
    clip: true

    property string message: ""
    property string bannerType: "info"  // "bank", "task", "info"

    function show(msg, type) {
        message = msg
        bannerType = type || "info"
        bannerText.text = msg
        slideIn.start()
    }

    function hide() {
        slideOut.start()
    }

    Behavior on height {
        NumberAnimation { duration: 200; easing.type: Easing.OutCubic }
    }

    NumberAnimation {
        id: slideIn
        target: bannerContent
        property: "x"
        from: bannerRoot.width; to: 0
        duration: 300
        easing.type: Easing.OutCubic
    }

    NumberAnimation {
        id: slideOut
        target: bannerContent
        property: "x"
        from: 0; to: bannerRoot.width
        duration: 250
        easing.type: Easing.InCubic
        onFinished: bannerText.text = ""
    }

    Rectangle {
        id: bannerContent
        anchors.fill: parent
        radius: 8
        color: {
            if (bannerType === "bank") return Qt.rgba(0.063, 0.725, 0.506, 0.1)
            if (bannerType === "task") return Qt.rgba(0.957, 0.620, 0.043, 0.1)
            return Qt.rgba(0.145, 0.388, 0.922, 0.1)
        }
        border.width: 1
        border.color: {
            if (bannerType === "bank") return Qt.rgba(0.063, 0.725, 0.506, 0.3)
            if (bannerType === "task") return Qt.rgba(0.957, 0.620, 0.043, 0.3)
            return Qt.rgba(0.145, 0.388, 0.922, 0.3)
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 12
            anchors.rightMargin: 12
            spacing: 8

            Label {
                text: {
                    if (bannerType === "bank") return "💰"
                    if (bannerType === "task") return "📋"
                    return "ℹ️"
                }
                font.pixelSize: 16
            }

            Label {
                id: bannerText
                Layout.fillWidth: true
                font.pixelSize: 13
                font.weight: Font.Medium
                color: "#1F2937"
                elide: Text.ElideRight
                maximumLineCount: 1
            }

            Label {
                text: "✕"
                font.pixelSize: 12
                color: "#6B7280"
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: bannerRoot.hide()
                }
            }
        }
    }
}
