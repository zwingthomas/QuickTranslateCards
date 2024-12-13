//
//  CustomToggleStyle.swift
//  QuickTranslateCards
//
//  Created by Thomas Zwinger on 12/13/24.
//

import SwiftUI

struct CustomToggleStyle: ToggleStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack {
            configuration.label
            Spacer()
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(configuration.isOn ? Color.green : Color.gray)
                    .frame(width: 50, height: 30)

                Circle()
                    .fill(Color.white)
                    .frame(width: 24, height: 24)
                    .offset(x: configuration.isOn ? 10 : -10)
                    .animation(.easeInOut(duration: 0.2), value: configuration.isOn)
            }
            .onTapGesture {
                configuration.isOn.toggle()
            }
        }
        .padding()
    }
}
