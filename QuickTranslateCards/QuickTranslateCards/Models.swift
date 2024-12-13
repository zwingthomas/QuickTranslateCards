//
//  Models.swift
//  QuickTranslateCards
//
//  Created by Thomas Zwinger on 12/13/24.
//

import Foundation

struct Word: Codable, Identifiable, Equatable {
    let id = UUID()
    var portuguese: String
    var english: String
    var weight_en_to_pt: Int
    var weight_pt_to_en: Int

    enum CodingKeys: String, CodingKey {
        case portuguese, english, weight_en_to_pt, weight_pt_to_en
    }
}
