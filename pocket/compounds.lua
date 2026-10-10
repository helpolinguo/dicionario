-- Hyphenation INSIDE the parts of a compound, for the pocket book.
--
-- LuaTeX hyphenates a word only where it follows glue. The part of a
-- compound that follows its own hyphen does not: « Muzik-instrumento » could
-- break after « Muzik- » and nowhere else, where « instrumento » alone breaks
-- in-stru-mento, and « bele-azurea » could not break inside « azurea ».
-- No primitive changes that: \hyphenationbounds 1, 2 and 3 and
-- \automatichyphenmode 2 were tried, and none hyphenates the parts. In a
-- column of 43 mm such a word is a block, and the line before it takes the
-- slack -- ultimato's first line stretched its spaces to 2.6 times their
-- width, waiting on « serio-lasta ».
--
-- So a glue of no width is laid after every hyphen that stands between two
-- letters, before the patterns run: the part that follows becomes a word, and
-- the patterns reach it. The glue is breakable, like the hyphen it follows,
-- and breaking there leaves the hyphen at the end of the line, as before;
-- unbroken, it is nothing. « 1-2 », « a--b » and a hyphen beside a bracket are
-- left alone: one side is not a letter.
--
-- Text set in Inter is left alone too: the headwords, and the phrases of the
-- sub-entries. A headword is never hyphenated -- it opens its paragraph, and
-- no glue precedes it -- and its compound must not start to be.

local GLYPH, GLUE = node.id("glyph"), node.id("glue")

local inter = {}
local function in_inter(f)
  if inter[f] == nil then
    local d = font.getfont(f)
    local name = d and string.lower((d.fullname or d.name or "") .. (d.psname or "")) or ""
    inter[f] = string.find(name, "inter", 1, true) ~= nil
  end
  return inter[f]
end

local function letter(n)
  return n ~= nil and n.id == GLYPH
     and unicode.utf8.match(unicode.utf8.char(n.char), "^%a$") ~= nil
end

luatexbase.add_to_callback("hyphenate", function(head, tail)
  for n in node.traverse_id(GLYPH, head) do
    if n.char == 45 and letter(n.prev) and letter(n.next) and not in_inter(n.font) then
      node.insert_after(head, n, node.new(GLUE))
    end
  end
  lang.hyphenate(head, tail)
end, "compound hyphenation")
