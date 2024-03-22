module Main where

import System.Environment
import System.Random
import System.IO
import Data.List.Split
import Data.List
import Control.Monad

type Grid = [[Char]]
{--
main :: IO ()
main = do
  hSetBuffering stdout NoBuffering
  putStrLn "1"
  _ <- hWaitForInput stdin (-1)
  line <- getLine
  putStrLn "2"
  loop

loop :: IO ()
loop = do
  _ <- hWaitForInput stdin (-1)
  line <- getLine
  putStrLn line
  loop
--}
main :: IO ()
main = do
  hSetBuffering stdout NoBuffering
  args <- getArgs
  let size = read $ head args
      numMines = size * size `div` 7
  rnd <- sequence $ replicate numMines newStdGen
  let 
    mines = makeGrid size rnd
    values = chunksOf size $ for size 0 mines
    visible = replicate size $ replicate size '.'
  guess (size * size - numMines)  values 8 visible 

guess :: Int -> Grid -> Int -> Grid -> IO ()
guess goal mines size visible = do
  if length (filter (/= '.') $ concat visible) == goal then do
    win visible
  else do
    putStrLn $ intercalate "n" visible
    response <- getLine
    let 
      (t:a:b:_) = splitOn " " response
      i = read b :: Int
      j = read a :: Int

    if t == "f" then 
      guess goal mines size (set i j 'F' visible)
    else case mines !! i !! j of 
      'X' -> lose mines
      '0' -> do
        let visible' = floodfill [(i, j)] mines visible [(i, j)]
        guess goal mines size visible'
      _   -> guess goal mines size (set i j (mines !! i !! j) visible)

floodfill :: [(Int, Int)]  -> Grid -> Grid -> [(Int, Int)] -> Grid
floodfill _ _ visible [] = visible
floodfill prev mines visible ((i, j):xs)
  | mines !! i !! j == 'X' = floodfill ((i,j):prev) mines (set i j (mines !! i !! j) visible) xs
  | mines !! i !! j /= '0' = floodfill ((i,j):prev) mines (set i j (mines !! i !! j) visible) xs
  | otherwise = floodfill (prev ++ new') mines (set i j '0' visible) (xs ++ new')
  where
    num = length visible
    adjacent = [(i+a, j+b) | a <- [-1..1], b <- [-1..1], a /= 0 || b /= 0]
    new = filter (\(a, b) -> a >= 0 && a < num && b >= 0 && b < num) adjacent
    new' = filter (`notElem` prev) new

win :: Grid -> IO ()
win visible = putStrLn $ "win " ++ intercalate "n" visible

lose :: Grid -> IO ()
lose visible = putStrLn $ "lose " ++ intercalate "n" visible

for :: Int -> Int -> Grid -> [Char]
for size num mines 
  | num == size * size = []
  | otherwise = countMine size mines i j : for size (num+1) mines
  where 
    i = num `div` size
    j = num `mod` size

countMine :: Int -> Grid-> Int -> Int -> Char
countMine _ grid i j
  | grid !! i !! j == 'X' = 'X'
countMine size grid i j = head $ show $ sum l
  where
    l = [if (grid !! a !! b) == 'X' then 1 else 0 | a <- [max 0 (i-1)..min (size-1) (i+1)], b <- [max 0 (j-1)..min (size-1) (j+1)]]

makeGrid :: Int -> [StdGen] -> Grid
makeGrid size rnd = foldl (fill size) grid rnd
  where 
    grid = replicate size $ replicate size '#'

fill :: Int -> Grid -> StdGen -> Grid
fill size grid rnd = set i j 'X' grid
  where  
    (i, r) = randomR (0, size-1) rnd :: (Int, StdGen)
    (j, _) = randomR (0, size-1) r :: (Int, StdGen)

set :: Int -> Int -> Char -> Grid -> Grid
set i j r grid = take i grid ++ [row'] ++ drop (i+1) grid
  where 
    row = grid !! i
    row' = take j row ++ [r] ++ drop (j+1) row
