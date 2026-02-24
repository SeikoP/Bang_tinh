pragma Singleton
import QtQuick

/**
 * Material 3 Theme Singleton for Warehouse Management App
 * 
 * Provides centralized color palette, typography, spacing, and elevation tokens.
 * Based on Material Design 3 with custom brand colors (Emerald + Slate).
 */
QtObject {
    id: theme

    // ========================
    // Color Palette — Brand
    // ========================
    readonly property color primary: "#10b981"         // Emerald-500
    readonly property color primaryHover: "#059669"     // Emerald-600
    readonly property color primaryLight: "#34d399"     // Emerald-400
    readonly property color primaryDark: "#047857"      // Emerald-700
    readonly property color primaryContainer: "#d1fae5" // Emerald-100

    readonly property color secondary: "#8B5CF6"        // Violet-500
    readonly property color secondaryContainer: "#ede9fe"

    readonly property color tertiary: "#14B8A6"         // Teal-500
    readonly property color tertiaryContainer: "#ccfbf1"

    // ========================
    // Color Palette — Surface
    // ========================
    readonly property color background: "#FFFFFF"
    readonly property color backgroundSecondary: "#F9FAFB"  // Gray-50
    readonly property color surface: "#FFFFFF"
    readonly property color surfaceVariant: "#F3F4F6"       // Gray-100
    readonly property color surfaceHover: "#FAFBFC"
    readonly property color surfaceTint: "#10b981"

    // ========================
    // Color Palette — Text
    // ========================
    readonly property color primaryText: "#FFFFFF"
    readonly property color primaryContainerText: "#064e3b"   // Emerald-900
    readonly property color secondaryText: "#FFFFFF"
    readonly property color backgroundText: "#1F2937"         // Gray-800
    readonly property color surfaceText: "#1F2937"            // Gray-800
    readonly property color surfaceVariantText: "#6B7280"     // Gray-500
    readonly property color textDisabled: "#9CA3AF"         // Gray-400

    // ========================
    // Color Palette — Status
    // ========================
    readonly property color success: "#10B981"
    readonly property color successContainer: "#d1fae5"
    readonly property color warningColor: "#F59E0B"  // Amber-500
    readonly property color warningContainer: "#fef3c7"
    readonly property color error: "#DC2626"          // Red-600
    readonly property color errorContainer: "#fee2e2"
    readonly property color info: "#2563EB"           // Blue-600
    readonly property color infoContainer: "#dbeafe"

    // ========================
    // Color Palette — Sidebar
    // ========================
    readonly property color sidebarBg: "#0f172a"          // Slate-900
    readonly property color sidebarText: "#94a3b8"        // Slate-400
    readonly property color sidebarItemHover: "#1e293b"   // Slate-800
    readonly property color sidebarItemActive: "#10b981"  // Emerald-500

    // ========================
    // Color Palette — Border & Outline
    // ========================
    readonly property color outline: "#E5E7EB"       // Gray-200
    readonly property color outlineHover: "#CBD5E1"  // Gray-300
    readonly property color outlineFocus: "#2563EB"  // Blue-600

    // ========================
    // Typography Scale (Material 3)
    // ========================
    readonly property QtObject typography: QtObject {
        // Display
        readonly property font displayLarge: Qt.font({ family: "Roboto", pixelSize: 57, weight: Font.Normal })
        readonly property font displayMedium: Qt.font({ family: "Roboto", pixelSize: 45, weight: Font.Normal })
        readonly property font displaySmall: Qt.font({ family: "Roboto", pixelSize: 36, weight: Font.Normal })
        // Headline
        readonly property font headlineLarge: Qt.font({ family: "Roboto", pixelSize: 32, weight: Font.Normal })
        readonly property font headlineMedium: Qt.font({ family: "Roboto", pixelSize: 28, weight: Font.Normal })
        readonly property font headlineSmall: Qt.font({ family: "Roboto", pixelSize: 24, weight: Font.Normal })
        // Title
        readonly property font titleLarge: Qt.font({ family: "Cabin", pixelSize: 22, weight: Font.Medium })
        readonly property font titleMedium: Qt.font({ family: "Cabin", pixelSize: 16, weight: Font.Medium })
        readonly property font titleSmall: Qt.font({ family: "Cabin", pixelSize: 14, weight: Font.Medium })
        // Body
        readonly property font bodyLarge: Qt.font({ family: "Roboto", pixelSize: 16, weight: Font.Normal })
        readonly property font bodyMedium: Qt.font({ family: "Roboto", pixelSize: 14, weight: Font.Normal })
        readonly property font bodySmall: Qt.font({ family: "Roboto", pixelSize: 12, weight: Font.Normal })
        // Label
        readonly property font labelLarge: Qt.font({ family: "Roboto", pixelSize: 14, weight: Font.Medium })
        readonly property font labelMedium: Qt.font({ family: "Roboto", pixelSize: 12, weight: Font.Medium })
        readonly property font labelSmall: Qt.font({ family: "Roboto", pixelSize: 11, weight: Font.Medium })
    }

    // ========================
    // Spacing Tokens (4px grid)
    // ========================
    readonly property int spacingXs: 4
    readonly property int spacingSm: 8
    readonly property int spacingMd: 16
    readonly property int spacingLg: 24
    readonly property int spacingXl: 32
    readonly property int spacingXxl: 48

    // ========================
    // Border Radius Tokens
    // ========================
    readonly property int radiusNone: 0
    readonly property int radiusSm: 4
    readonly property int radiusMd: 8
    readonly property int radiusLg: 12
    readonly property int radiusXl: 16
    readonly property int radiusFull: 9999

    // ========================
    // Elevation (shadow opacity)
    // ========================
    readonly property int elevation0: 0
    readonly property int elevation1: 1
    readonly property int elevation2: 3
    readonly property int elevation3: 6
    readonly property int elevation4: 8
    readonly property int elevation5: 12

    // ========================
    // Layout Constants
    // ========================
    readonly property int sidebarWidth: 72          // Collapsed rail
    readonly property int sidebarExpandedWidth: 200 // Expanded rail  
    readonly property int headerHeight: 64
    readonly property int toolbarHeight: 56
    readonly property int fabSize: 56
    readonly property int fabMiniSize: 40
    readonly property int iconSize: 24
    readonly property int iconSizeLarge: 32

    // ========================
    // Animation Durations (ms)
    // ========================
    readonly property int animFast: 150
    readonly property int animNormal: 250
    readonly property int animSlow: 400
    readonly property int animEasing: Easing.OutCubic

    // ========================
    // Helper Functions
    // ========================
    function withAlpha(baseColor, alpha) {
        return Qt.rgba(baseColor.r, baseColor.g, baseColor.b, alpha)
    }

    function elevationColor(level) {
        // Material 3 tonal elevation — surface + primary tint
        var alpha = level * 0.02
        return Qt.rgba(surfaceTint.r, surfaceTint.g, surfaceTint.b, alpha)
    }
}
