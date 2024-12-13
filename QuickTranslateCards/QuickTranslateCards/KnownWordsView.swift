//
//  KnownWordsView.swift
//  QuickTranslateCards
//
//  Created by Thomas Zwinger on 12/13/24.
//

import SwiftUI

struct KnownWordsView: View {
    @ObservedObject var manager: WordManager
    var showEnglishFirst: Bool
    
    var body: some View {
        NavigationView {
            List {
                ForEach(manager.knownWords()) { word in
                    VStack(alignment: .leading, spacing: 5) {
                        Text("Portuguese: \(word.portuguese)")
                            .font(.headline)
                        Text("English: \(word.english)")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    .padding(.vertical, 5)
                    .onTapGesture {
                        // Mark this word as unknown = 9
                        manager.updateWord(word, rating: 9)
                    }
                }
            }
            .navigationBarTitle("Known Words", displayMode: .inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Done") {
                        // Close the sheet
                        if let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene {
                            scene.windows.first?.rootViewController?.dismiss(animated: true, completion: nil)
                        }
                    }
                }
            }
        }
    }
}
