//
//  SettingsView.swift
//  QuickTranslateCards
//
//  Created by Thomas Zwinger on 12/13/24.
//

import SwiftUI

struct SettingsView: View {
    @State private var showEnglishFirst = true

    var body: some View {
        Toggle("Show English First", isOn: $showEnglishFirst)
            .toggleStyle(CustomToggleStyle())
            .padding()
    }
}
