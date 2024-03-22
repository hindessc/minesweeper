CABAL=cabal
EXECUTABLE_NAME=mineSweeper

dev: build
	ln -sf $$(cabal exec -- which ${EXECUTABLE_NAME}) ${EXECUTABLE_NAME}

build:
	cabal build

clean:
	cabal clean
	rm ${EXECUTABLE_NAME}
