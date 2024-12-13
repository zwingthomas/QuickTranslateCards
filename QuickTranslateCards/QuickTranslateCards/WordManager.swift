//
//  WordManager.swift
//  QuickTranslateCards
//
//  Created by Thomas Zwinger on 12/13/24.
//

import Foundation

class WordManager: ObservableObject {
    @Published var words: [Word] = []
    @Published var showEnglishFirst: Bool = false  // toggle for language order

    private let fileName = "words.json"
    
    init() {
        loadWords()
    }
    
    private func getDocumentsDirectory() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
    
    private var wordsFileURL: URL {
        return getDocumentsDirectory().appendingPathComponent(fileName)
    }
    
    func loadWords() {
        let fm = FileManager.default
        if !fm.fileExists(atPath: wordsFileURL.path) {
            if let bundleURL = Bundle.main.url(forResource: "words", withExtension: "json") {
                try? fm.copyItem(at: bundleURL, to: wordsFileURL)
            } else {
                words = []
                return
            }
        }
        
        do {
            let data = try Data(contentsOf: wordsFileURL)
            let decoded = try JSONDecoder().decode(WordsData.self, from: data)
            words = decoded.words
        } catch {
            print("Failed to load words: \(error)")
            words = []
        }
    }
    
    func saveWords() {
        let data = WordsData(words: words)
        do {
            let encoded = try JSONEncoder().encode(data)
            try encoded.write(to: wordsFileURL, options: [.atomicWrite])
        } catch {
            print("Failed to save words: \(error)")
        }
    }
    
    func updateWord(_ word: Word, rating: Int) {
        guard let index = words.firstIndex(of: word) else { return }
        
        if showEnglishFirst {
            words[index].weight_en_to_pt = rating
        } else {
            words[index].weight_pt_to_en = rating
        }
        
        saveWords()
    }
    
    func randomWord() -> Word? {
        guard !words.isEmpty else { return nil }
        
        let weights = words.map { showEnglishFirst ? $0.weight_en_to_pt : $0.weight_pt_to_en }
        let total = weights.reduce(0, +)
        
        if total == 0 {
            return words.randomElement()
        }
        
        let r = Int.random(in: 0..<total)
        var cumulative = 0
        for (i, w) in weights.enumerated() {
            cumulative += w
            if r < cumulative {
                return words[i]
            }
        }
        
        return words.randomElement()
    }
    
    func knownWords() -> [Word] {
        // Known means rating = 0 for the current mode
        if showEnglishFirst {
            return words.filter { $0.weight_en_to_pt == 0 }
        } else {
            return words.filter { $0.weight_pt_to_en == 0 }
        }
    }
}
