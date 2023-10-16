#CC=clang-3.8
CC=g++
CPPFLAGS=--std=c++11 -Wall -pedantic -Werror -g -fopenmp
#CFLAGS=--std=gnu99 -Wall -pedantic -Werror -g -pg -fopenmp
#RELFLAGS=-Ofast
RELFLATS=-O0
DEBUGFLAGS=-DDEBUG -no-pie -pg -O0
GIT_COMMIT=$(shell ./scripts/git_status.sh)

LIBS=-lrt -lm
DEPS=sim.hpp print.hpp command.hpp network.hpp arch.hpp description.hpp
OBJ=main.o sim.o command.o network.o arch.o description.o
DEBUGDIR=debug
RELDIR=release

RELOBJ=$(addprefix $(RELDIR)/,$(OBJ))
RELEXE=$(RELDIR)/sim
DEBUGOBJ=$(addprefix $(DEBUGDIR)/,$(OBJ))
DEBUGEXE=$(DEBUGDIR)/sim

.PHONY: all sim release debug clean prep

all: prep sim

sim: release
	cp $(RELEXE) sim

release: $(RELEXE)

debug: prep $(DEBUGEXE)

$(RELDIR)/%.o: %.cpp $(DEPS)
	$(CXX) -c -o $@ $< $(CPPFLAGS) $(RELFLAGS) -DGIT_COMMIT=\"$(GIT_COMMIT)\"

$(RELEXE): $(RELOBJ)
	$(CXX) -o $@ $^ $(CPPFLAGS) $(RELFLAGS) $(LIBS)

$(DEBUGDIR)/%.o: %.cpp $(DEPS)
	$(CXX) -c -o $@ $< $(CPPFLAGS) $(DEBUGFLAGS) -DGIT_COMMIT=\"$(GIT_COMMIT)\"

$(DEBUGEXE): $(DEBUGOBJ)
	$(CXX) -o $@ $^ $(CPPFLAGS) $(DEBUGFLAG) $(LIBS)

clean:
	rm -f $(RELEXE)
	rm -f $(DEBUGEXE)
	rm -f $(RELOBJ)
	rm -f $(DEBUGOBJ)

prep:
	@mkdir -p $(RELDIR) $(DEBUGDIR) runs
